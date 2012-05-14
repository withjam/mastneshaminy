from pyramid.view import view_config
from pyramid.response import Response
from utils import read_sign
from utils import sig2b64
from utils import get_sign_path

def json_error(msg=None):
    return {'status':'Error','msg':msg}
    
def json_ok(data=None):
    return {'status':'OK','data':data}

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
    from pyramid.httpexceptions import HTTPFound
    entry = post_signature(request)
    if entry['status'] == 'OK':
        eid = entry['data']['_id']
        return HTTPFound(location='/signature/'+str(eid)+'.png')
    request.session.flash(entry['msg'])
    return HTTPFound(location=request.route_url('petition'))
    
@view_config(route_name='viewsign', request_method='GET')
def view_signature(request):
    sign = read_sign(request.matchdict['filename'])
    file_response = Response(content_type='image/png',
                        body=sign)
    return file_response
    
""" API Handlers """
@view_config(route_name='postSign', renderer='jsonp', request_method='POST')
def post_signature(request):
    if 'fn' not in request.params:
        return json_error('Full Name is required')
    b64 = request.params['b64'] if 'b64' in request.params else None
    if 'output' in request.params:
        b64 = sig2b64(request.params['output'])
    if b64 is None:
        return json_error('Signature is required')
    entry = {
        'fn': request.params['fn'],
        'par': request.params['par'] == 'yes' if 'par' in request.params else False,
        'res': request.params['res'] == 'yes' if 'res' in request.params else False,
        'tea': request.params['tea'] == 'yes' if 'tea' in request.params else False,
        'a': request.params['a'] if 'a' in request.params else None,
        'em': request.params['em'] if 'em' in request.params else None,
        'z': request.params['z'] if 'par' in request.params else None,
        'b64': b64
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
    if 'ln' not in request.params or 'fn' not in request.params:
        errors.append('Parent/Guardian Name required')
    if 'em' not in request.params:
        errors.append('Email is required')
    if 'a1' not in request.params:
        errors.append('Address is required')
    if 'z' not in request.params:
        errors.append('Zip code is required')
    if 'children' is '0':
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
        'ln': request.params['ln'],
        'fn': request.params['fn'],
        'em': request.params['em'],
        'a1': request.params['a1'],
        'a2': request.params['a2'] if 'a2' in request.params else None,
        'z': request.params['z'],
        'c': children
    }
    request.db.applicants.insert(data)
    return json_ok(data)
