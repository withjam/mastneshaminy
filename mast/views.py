from pyramid.view import view_config
from utils import sig2b64

def json_error(msg=None):
    return {'status':'Error','msg':msg}
    
def json_ok(data=None):
    return {'status':'OK','data':data}

""" WWW Handlers """
@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'mast','geoip':request.geoip,'ip':request.remote_addr}
    
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
        'par': request.params['par'] == 'yes',
        'res': request.params['res'] == 'yes',
        'tea': request.params['tea'] == 'yes',
        'a1': request.params['a1'],
        'a2': request.params['a2'] if 'a2' in request.params else None,
        'z': request.params['z'],
        'b64': b64
    }
    request.db.signatures.insert(entry)
    # write it out to a file as backup
    fname = str(entry['_id'])+'.png'
    img = open('signatures/'+fname,'wb')
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
