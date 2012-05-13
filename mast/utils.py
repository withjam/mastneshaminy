import random
import hashlib
import StringIO
from base64 import b64encode
from signpad2image import s2i

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