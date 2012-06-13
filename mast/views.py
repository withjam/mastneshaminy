from datetime import datetime
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from utils import read_sign
from utils import read_upload_file
from utils import sig2b64
from utils import get_sign_path
from utils import get_upload_path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import logging
from bson.code import Code
from bson.objectid import ObjectId
log = logging.getLogger(__name__)

def init_mimetypes(mimetypes):
    # this is a function so it can be unittested
    if hasattr(mimetypes, 'init'):
        mimetypes.init()
        return True
    return False

def prep_mongodoc(doc):
    doc['_id'] = str(doc['_id'])
    if 'utc' in doc:
        doc['utc'] = doc['utc'].isoformat()
    return doc
    
def prep_mongocursor(cur):
    return [ prep_mongodoc(doc) for doc in cur]

def create_response(title='Neshaminy Charter Info',desc='',keywords=''):
    return {'title': title, 'description': desc, 'keywords': keywords}

def json_error(msg=None):
    return {'status':'Error','msg':msg}
    
def json_ok(data=None):
    return {'status':'OK','data':data}
    
def add_utc():
    return datetime.utcnow()

def add_geo(request):
    lat = float(request.params['lat']) if 'lat' in request.params else 0
    lon = float(request.params['lon']) if 'lon' in request.params else 0
    if hasattr(request,'geoip') and request.geoip is not None:
        lat = request.geoip['latitiude'] if lat is 0 else lat
        lon = request.geoip['longitutde'] if lon is 0 else lon
    return [lat,lon]
    
mapCnt = Code('function() { emit(this.dtype,this.cnt || 0) }')
reduceCnt = Code('function(k,v) { var t = 0;  for(var i=0;i < v.length;i++) { t+=v[i]; } return t; }')
def reduceups(request,split=False):
    result = request.db.uploads.map_reduce(mapCnt,reduceCnt,'countresults')
    return result

def getsigcount(request,split=False):
    dcnt = request.db.signatures.count()
    ucnt = 0
    for doc in reduceups(request).find({'_id':'pet'}):
        ucnt += doc['value']
    tot = ucnt + dcnt
    return int(tot) if not split else {'tot':int(tot),'dcnt':int(dcnt),'ucnt':int(ucnt)}
    
def getappcount(request,split=False):
    dcnt = 0
    for doc in request.db.applicants.find():
        dcnt += len(doc['c'])
    result = reduceups(request)
    ucnt = 0
    for doc in result.find({'_id':'app'}):
        ucnt += doc['value']
    tot = ucnt + dcnt
    return int(tot) if not split else {'tot':int(tot),'dcnt':int(dcnt),'ucnt':int(ucnt)}
    
afmap = Code('function() { this.c.forEach(function(c) { if(c.s === "m" || c.s === "Boy") { emit("Boys",1); } else { emit("Girls",1); } if (c.g === "K" || parseInt(c.g) === 0) { emit(0,1); } else { emit(parseInt(c.g),1); } }); }')
afreduce = Code('function(k,v) { var t = 0;  for(var i=0;i < v.length;i++) { t+=v[i]; } return t; }')
def getappfacets(request):
    coll = request.db.applicants.map_reduce(afmap,afreduce,'appfacets')
    facets = { 'grades': [], 'genders': [] };
    for doc in coll.find():
        if doc['_id'] in ['Boys','Girls']:
            facets['genders'].append({'id':doc['_id'], 'value': doc['value']})
        else:
            facets['grades'].append({'id': doc['_id'] if doc['_id'] != 0 else 'K', 'value': int(doc['value'])})
    return facets
    
def getsiglocs(request):
    locs = []
    for doc in request.db.signatures.find():
        if 'geo' in doc and doc['geo'][0] != 0:
            locs.append({'lat':doc['geo'][0],'lon':doc['geo'][1]})
        
    return locs
    
def missing(prop,obj):
    val = obj[prop] if prop in obj else None
    if val is not None and len(val.strip()) > 0:
        return False
    return True
    
def missingparam(prop,req):
    return missing(prop,req.params)

""" WWW Handlers """
@view_config(route_name='oldhome', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'mast','geoip':request.geoip,'ip':request.remote_addr}
    
@view_config(route_name='home', renderer='templates/home.pt')
def web_home(request):
    resp = create_response('Homepage',desc='Help us bring a MaST Community Charter to the Neshaminy School District',keywords='Neshaminy Charter School,MaST Charter School,Neshaminy Charter Info,Homepage')
    resp['geoip'] = request.geoip
    resp['sigcnt'] = getsigcount(request)
    return resp
    
@view_config(route_name='petition', renderer='templates/petition.pt', request_method='GET')
def petition_form(request):
    resp = create_response('Sign the Petition',desc='Sign the Petition to urge the Neshaminy School Board to approve a MaST Charter School!',keywords='MaST Petition, Neshaminy Charter School Petition,online charter school petition,math science and technology charter,neshaminy math petition')
    resp['messages'] = request.session.pop_flash()
    return resp
    
@view_config(route_name='petition', request_method='POST')
def petition_thanks(request):
    entry = post_signature(request)
    if entry['status'] == 'OK':
        eid = entry['data']['_id']
        em = entry['data']['em'] if 'em' in entry['data'] else ''
        request.session.flash('signing our petition','src')
        request.session.flash(em,'em')
        return HTTPFound(location='/thanks.html?eid='+str(eid))
    request.session.flash(entry['msg'])
    return HTTPFound(location=request.route_url('petition'))
    
@view_config(route_name='viewsign', request_method='GET')
def view_signature(request):
    sign = read_sign(request.matchdict['filename'])
    file_response = Response(content_type='image/png',
                        body=sign)
    return file_response
    
@view_config(route_name='viewupload', request_method='GET')
def view_uploaded_file(request):
    eid = request.matchdict['filename']
    ext = request.matchdict['ext']
    ufile = read_upload_file(eid+'.'+ext)
    file_response = Response(content_type=ent['mtype'],
                        body=ufile)
    return file_response
    
@view_config(route_name='thanks', request_method='GET',renderer='templates/thanks.pt')
def thanks_page(request):
    fl = request.session.pop_flash('src')
    msg = fl[0] if len(fl) > 0 else 'your support'
    fl = request.session.pop_flash('em')
    em = fl[0] if len(fl) > 0 else ''
    resp = create_response(title='Thank You!')
    resp['source'] = msg
    resp['em'] = em
    return resp
    
@view_config(route_name='apply', renderer='templates/apply.pt', request_method='GET')
def apply_form(request):
    resp = create_response('Pre-Enroll in Neshaminy MaST Charter School',desc='Complete our Pre-Application form to reserve a spot for your children in MaST Neshaminy! No obligation to enroll but it helps us judge interest.',keywords='Neshaminy Charter School Pre-Application,early application form,MaST Neshaminy Enrollment,online enrollment form,charter school enrollment form,charter school pre-application,MaST application,MaST Neshaminy Application')
    resp['messages'] = request.session.pop_flash()
    return resp
    
@view_config(route_name='apply', request_method='POST')
def post_apply_form(request):
    entry = post_application(request)
    if entry['status'] == 'OK':
        em = entry['data']['em'] if 'em' in entry['data'] else ''
        request.session.flash('pre-applying','src',)
        request.session.flash(em,'em')
        return HTTPFound(location='/thanks.html')
    request.session.flash(entry['msg'])
    return HTTPFound(location=request.route_url('apply'))
    
@view_config(route_name='about', renderer='templates/about.pt')
def view_about(request):
    return create_response(title='About the MaST Community Charter System',desc='Information about the MaST Charter School and what a Neshaminy Charter School would mean to the Neshaminy School District',keywords='About MaST Charter, About MaST Neshaminy,MaST Neshaminy Charter School,Neshaminy MaST Charter School')
    
@view_config(route_name='privacy', renderer='templates/privacy.pt')
def view_privacy(request):
    return create_response(title='Privacy Policy')
    
@view_config(route_name='why', renderer='templates/why.pt')
def view_why(request):
    return create_response(title='Why MaST Charter is good for Neshaminy',desc='A presentation explaining why MaST Community Charter School will provide a great benefit to Neshaminy School Students',keywords='Why a Mast Charter School,Mast charter for neshaminy,why a charter school,why neshaminy')
    
@view_config(route_name='upload', renderer='templates/uploads.pt', request_method='GET')
def upload_form(request):
    resp = create_response(title='Upload Paper Documents')
    resp['messages'] = request.session.pop_flash()
    resp['success'] = request.session.pop_flash('success')
    return resp
    
@view_config(route_name='upload', request_method='POST')
def post_upload(request):
    entry = upload_doc(request)
    if entry['status'] == 'OK':
        em = entry['data']['em'] if 'em' in entry['data'] else ''
        request.session.flash(str(entry['data']['_id']),'success')
    else:
        request.session.flash(entry['msg'])
    return HTTPFound(location=request.route_url('upload'))
    
@view_config(route_name="dashboard", request_method="GET", renderer="templates/dashboard.pt")
def view_dashboard(request):
    resp = create_response(title='Dashboard')
    resp['sig'] = getsigcount(request,True)
    resp['sig']['locs'] = getsiglocs(request)
    resp['app'] = getappcount(request,True)
    resp['app']['facets'] = getappfacets(request)
    return resp
    
@view_config(route_name="cleanlist", request_method="GET", renderer="templates/clean.pt")
def view_clean_list(request):
    resp = create_response(title='Clean Uploaded Documents')
    resp['docs'] = []
    # get all the uploads
    for doc in request.db.uploads.find():
        if 'names' not in doc or len(doc['names']) < doc['cnt']:
            resp['docs'].append(prep_mongodoc(doc))
    return resp
    
@view_config(route_name="cleandoc", request_method="GET", renderer="templates/cleandoc.pt")
def clean_doc_form(request):
    doc = request.db.uploads.find_one({'_id':ObjectId(request.matchdict['eid'])})
    resp = create_response(title='Enter Document Names')
    resp['id'] = request.matchdict['eid']
    resp['doc'] = doc
    return resp
    
doctypes = ['image/png','image/jpeg','application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document']
""" API Handlers """
def upload_doc(request):
    errors = []
    if missingparam('name',request):
        errors.append('Your Name is required')
    if request.params['docfile'] is None:
        errors.append('A file is required')
    if request.params['docfile'].filename is None:
        errors.append('The filename was missing')
    if len(errors) == 0:
        init_mimetypes(mimetypes)
        fname = request.params['docfile'].filename
        mtype = mimetypes.guess_type(fname)
        if mtype[0] not in doctypes:
            errors.append('File is not a valid format.  Please upload .zip, .pdf, or .doc files.')
    if len(errors):
        return json_error(errors)
    ext = mimetypes.guess_extension(mtype[0])
    entry = {
        'who': request.params['name'],
        'dtype': request.params['dtype'],
        'mtype': mtype[0],
        'menc': mtype[1],
        'ext': ext,
        'cnt': int(request.params['count']) if 'count' in request.params else 1,
        'utc': add_utc(),
        'geo': add_geo(request)
    }
    request.db.uploads.insert(entry)
    # write it out to a file as backup
    input_file = request.POST['docfile'].file
    fpath = get_upload_path(str(entry['_id']),ext)
    output_file = open(fpath, 'wb')

    # Finally write the data to the output file
    input_file.seek(0)
    while 1:
        data = input_file.read(2<<16)
        if not data:
            break
        output_file.write(data)
    output_file.close()
    return json_ok(prep_mongodoc(entry))

@view_config(route_name='emailShare', renderer='jsonp', request_method='POST')
def share_email(request):
    errors = []
    if missingparam('from',request):
        errors.append('From address is required')
    if missingparam('to',request):
        errors.append('To address is required')
    if len(errors) > 0:
        return json_error(errors)
    fromAddr = request.params['from']
    toAddr = request.params['to']
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Help Me Bring MaST Charter School to Neshaminy!'
    msg['From'] = fromAddr
    msg['To'] = toAddr
    text = "Help me bring the MaST Charter School to the Neshaminy School District!\nThe MaST Community Charter, already operating in NE Philadelphia, has a fantastic record of excellence.  MaST places a high value on science and technology while giving all students the hands-on instruction that fosters a great learning environment.\nYou can learn more, and sign the petition, by visiting http://www.NeshaminyCharter.info?src=emailsh"
    html = """\
    <html>
      <head></head>
      <body>
        <p><strong>Help me bring the MaST Charter School to the Neshaminy School District!</strong></p>
        <p>The MaST Community Charter, already operating in NE Philadelphia, has a fantastic record of excellence.  MaST places a high value on science and technology while giving all students the hands-on instruction that fosters a great learning environment.</p>
        <p>You can learn more, and sign the petition, by visiting the <a href="http://www.NeshaminyCharter.info?src=emailsh">NeshaminyCharter.info</a> website.</p>
      </body>
    </html>
    """
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    request.mailer.sendmail(fromAddr,toAddr,msg.as_string())

@view_config(route_name='postSign', renderer='jsonp', request_method='POST')
def post_signature(request):
    log.info('signature posted')
    errors = []
    if missingparam('fn',request):
        errors.append('Full Name is required')
    b64 = request.params['b64'] if 'b64' in request.params else None
    if 'output' in request.params:
        b64 = sig2b64(request.params['output'])
    if b64 is None:
        errors.append('Signature is required')
    if missingparam('z',request):
        errors.append('Zipcode is required')
    if len(errors) > 0:
        return json_error(errors)
    entry = {
        'fn': request.params['fn'],
        'par': request.params['par'] == 'yes' if 'par' in request.params else False,
        'res': request.params['res'] == 'yes' if 'res' in request.params else False,
        'tea': request.params['tea'] == 'yes' if 'tea' in request.params else False,
        'a': request.params['a'] if 'a' in request.params else None,
        'em': request.params['em'] if 'em' in request.params else None,
        'z': request.params['z'] if 'par' in request.params else None,
        'src': request.params['src'] if 'src' in request.params else 'web',
        'utc': add_utc(),
        'geo': add_geo(request)
        #'b64': b64
    }
    request.db.signatures.insert(entry)
    # write it out to a file as backup
    fpath = get_sign_path(str(entry['_id']))
    img = open(fpath,'wb')
    img.write(b64.decode('base64'))
    img.close()
    return json_ok(prep_mongodoc(entry))
    
@view_config(route_name='postApp', renderer='jsonp', request_method='POST')
def post_application(request):
    log.info('application posted')
    errors = []
    if missingparam('fn',request):
        errors.append('Parent/Guardian Name required')
    if missingparam('em',request):
        errors.append('Email is required')
    if missingparam('a',request):
        errors.append('Address is required')
    if missingparam('z',request):
        errors.append('Zip code is required')
    if request.params['children'] == '0':
        errors.append('At least one child is required')
    if len(errors) > 0:
        return json_error(errors)
    children = []
    for i in range(int(request.params['children'])):
        croot = 'c'+str(i+1)
        child = {
            'n': request.params[croot+'n'],
            'g': request.params[croot+'g'],
            's': request.params[croot+'s'],
            'b': request.params[croot+'b']
        }
        children.append(child)
    data = {
        'fn': request.params['fn'],
        'em': request.params['em'],
        'res': request.params['res'] == 'yes' if 'res' in request.params else False,
        'a': request.params['a'],
        'a2': request.params['a2'] if not missingparam('a2',request) else None,
        'z': request.params['z'],
        'c': children,
        'src': request.params['src'] if 'src' in request.params else 'web',
        'geo': add_geo(request),
        'utc': add_utc()
    }
    request.db.applicants.insert(data)
    return json_ok(prep_mongodoc(data))
    
@view_config(route_name='appError', renderer='jsonp', request_method='POST')
def post_errors(request):
    log.info('receiving error')
    if missingparam('info', request):
        return json_error('error info not provided')
    data = {
        'rtype': request.matchdict['rtype'],
        'info': request.params['info'],
        'utc': add_utc()
    }
    request.db.apperrors.insert(data);
    return json_ok('error logged')
 
@view_config(route_name='appError', renderer='jsonp', request_method='GET')
def view_errors(request):
    return json_ok(prep_mongocursor(request.db.apperrors.find()))
