from datetime import datetime
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from utils import read_sign
from utils import sig2b64
from utils import get_sign_path

def json_error(msg=None):
    return {'status':'Error','msg':msg}
    
def json_ok(data=None):
    return {'status':'OK','data':data}
    
def add_utc():
    return datetime.utcnow()

def add_geo(request):
    lat = float(request.params['lat']) if 'lat' in request.params else 0
    lon = float(request.params['lon']) if 'lon' in request.params else 0
    if 'jkjkgeoip' in request:
        lat = request.geoip['latitiude'] if lat is 0 else lat
        lon = request.geoip['longitutde'] if lon is 0 else lon
    return [lat,lon]
    
def missing(prop,obj):
    val = obj[prop] if prop in obj else None
    if val is not None and len(val.strip()) > 0:
        return False
    return True
    
def missingparam(prop,req):
    return missing(prop,req.params)

""" WWW Handlers """
@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'mast','geoip':request.geoip,'ip':request.remote_addr}
    
@view_config(route_name='realhome', renderer='templates/home.pt')
def web_home(request):
    return {'geoip': request.geoip}
    
@view_config(route_name='petition', renderer='templates/petition.pt', request_method='GET')
def petition_form(request):
    return {'title': 'Sign the Petition','messages':request.session.pop_flash()}
    
@view_config(route_name='petition', request_method='POST')
def petition_thanks(request):
    entry = post_signature(request)
    if entry['status'] == 'OK':
        eid = entry['data']['_id']
        request.session.flash('signing our petition')
        return HTTPFound(location='/thanks.html?eid='+str(eid))
    request.session.flash(entry['msg'])
    return HTTPFound(location=request.route_url('petition'))
    
@view_config(route_name='viewsign', request_method='GET')
def view_signature(request):
    sign = read_sign(request.matchdict['filename'])
    file_response = Response(content_type='image/png',
                        body=sign)
    return file_response
    
@view_config(route_name='thanks', request_method='GET',renderer='templates/thanks.pt')
def thanks_page(request):
    fl = request.session.pop_flash()
    msg = fl[0] if len(fl) > 0 else 'your support'
    return {'source': msg}
    
@view_config(route_name='apply', renderer='templates/apply.pt', request_method='GET')
def apply_form(request):
    return {'title': 'Pre-Enroll in Neshaminy MaST Charter School', 'messages': request.session.pop_flash()}
    
@view_config(route_name='apply', request_method='POST')
def post_apply_form(request):
    entry = post_application(request)
    if entry['status'] == 'OK':
        request.session.flash('pre-applying')
        return HTTPFound(location='/thanks.html')
    request.session.flash(entry['msg'])
    return HTTPFound(location=request.route_url('apply'))
    
""" API Handlers """
@view_config(route_name='postSign', renderer='jsonp', request_method='POST')
def post_signature(request):
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
    return json_ok(entry)
    
@view_config(route_name='postApp', renderer='jsonp', request_method='POST')
def post_application(request):
    errors = []
    if missingparam('fn',request):
        errors.append('Parent/Guardian Name required')
    if missingparam('em',request):
        errors.append('Email is required')
    if missingparam('a1',request):
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
            'g': int(request.params[croot+'g']),
            's': request.params[croot+'s'],
            'b': request.params[croot+'b']
        }
        children.append(child)
    data = {
        'fn': request.params['fn'],
        'em': request.params['em'],
        'a1': request.params['a1'],
        'a2': request.params['a2'] if not missingparam('a2',request) else None,
        'z': request.params['z'],
        'c': children,
        'geo': add_geo(request),
        'utc': add_utc()
    }
    request.db.applicants.insert(data)
    return json_ok(data)
