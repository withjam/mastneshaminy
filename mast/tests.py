import unittest
import pymongo

from pyramid import testing
from mast import signpad2image

db = None

def getDB(dbname="masttest",uri="mongodb://staff.mongohq.com:10052"):
    global db
    if db is None:
        conn = pymongo.Connection(uri)
        db = conn[dbname]
        db.authenticate('dbuser','dbpass')
    return db

def getRequest(matchdict=None,**kvars):
    request = testing.DummyRequest(**kvars)
    request.db = getDB()
    request.matchdict = matchdict
    return request

class AppTests(unittest.TestCase):
    def setUp(self):
        getDB()
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_post_signature(self):
        from .views import post_signature
        req = getRequest(matchdict=None,params=dict(res='yes',par='no',tea='no',fn='Full Name',a='Address',z='19056'),post=True)
        res = post_signature(req)
        self.assertIn('status',res)
        self.assertEquals(res['status'],'Error')
        self.assertEqual(res['msg'],'Signature is required')
        sig64f = open('mast/test.b64')
        sig64 = sig64f.read()
        sig64f.close()
        req = getRequest(matchdict=None,params=dict(b64=sig64,res='yes',par='no',tea='no',fn='Full Name',a='Address',em='email',z='19056'),post=True)
        res = post_signature(req)
        self.assertEquals(res['status'],'OK')
        sigjf = open('mast/test.signpad')
        sigj = sigjf.read()
        sigjf.close()
        req = getRequest(matchdict=None,params=dict(output=sigj,res='yes',par='no',tea='no',fn='Full Name',a='Address Line 1',em='email',z='19056'),post=True)
        res = post_signature(req)
        self.assertEquals(res['status'],'OK')
        
    def test_pre_apply(self):
        from .views import post_application
        req = getRequest(matchdict=None,post=True)
        res = post_application(req)
        self.assertIn('status',res)
        self.assertEquals(res['status'],'Error')
        req = getRequest(matchdict=None,params=dict(z='19047',em='email',fn='First',ln='Last',children='1',c1n='Child',c1g='5',c1s='m',c1b='12/7/1976',ph='1234567890',a1='Address 1',a2='Address 2'),post=True)
        res = post_application(req)
        self.assertIn('status',res)
        self.assertEqual(res['status'],'OK')
