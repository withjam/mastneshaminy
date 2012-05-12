import unittest
import pymongo

from pyramid import testing

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

