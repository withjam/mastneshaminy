import random
import os
import hashlib
import StringIO
from base64 import b64encode
from signpad2image import s2i

_here = os.path.dirname(__file__)

def get_upload_path(name,ext):
    path = os.path.join(_here, 'uploads', name+ext)
    return path

def get_sign_path(name):
    path = os.path.join(_here, 'signatures', name+'.png')
    return path

# _icon = /app/location/myapp/static/favicon.ico
def read_sign(name):
    sign = open(os.path.join(
             _here, 'signatures', name+'.png')).read()
    return sign
    
#name includes extension for uploads
def read_upload_file(name,ext):
    ufile = open(get_upload_path(name,ext)).read()
    return ufile

def pencrypt(pwd):
    salt = ''.join(random.choice('bcdefghijklmnopqrstvwxyz0123456789') for i in range(6))
    h = hashlib.sha224()
    h.update(salt)
    h.update(pwd)
    return salt + h.hexdigest()
    
def pmatch(pwd,pwdenc):
    salt = pwdenc[:6]
    h = hashlib.sha224()
    h.update(salt)
    h.update(pwd)
    return pwdenc == salt + h.hexdigest()
    
def sig2b64(sig):
    img = s2i(sig)
    output = StringIO.StringIO()
    img.save(output,'PNG')
    b64 = b64encode(output.getvalue())
    output.close()
    return b64