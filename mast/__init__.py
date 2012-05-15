from pyramid.config import Configurator
from pyramid.events import subscriber
from pyramid.events import NewRequest
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.renderers import JSONP
import pymongo
import pygeoip
from bson import json_util


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    my_session_factory = UnencryptedCookieSessionFactoryConfig('neshmast')
    config = Configurator(settings=settings,session_factory = my_session_factory)
    db_uri = settings['db_uri']
    conn = pymongo.Connection(db_uri,tz_aware=True)
    db = conn[settings['db_name']]
    if ('db_user' in settings):
        db.authenticate(settings['db_user'],settings['db_pass'])
    config.registry.db = db
    config.add_renderer('jsonp', JSONP(param_name='jsonp'))
    config.registry.settings['db_conn'] = conn
    config.add_subscriber(add_mongo_db, NewRequest)
    gi = pygeoip.GeoIP(settings['geoip_dat'], pygeoip.MEMORY_CACHE)
    config.registry.settings['pygeo'] = gi
    config.add_subscriber(add_geoip, NewRequest)
    config.add_static_view('static', 'static', cache_max_age=3600)
    # Web Routes
    config.add_route('home', '/')
    config.add_route('realhome', '/home')
    config.add_route('petition', '/petition')
    config.add_route('viewsign', '/signature/{filename}.png')
    config.add_route('enroll', '/enroll')
    # API Routes
    config.add_route('postApp','/json/applicant')
    config.add_route('postSign','/json/sign')
    config.scan()
    return config.make_wsgi_app()
    
def add_mongo_db(event):
    db = event.request.registry.db
    event.request.db = db
def add_geoip(event):
    gi = event.request.registry.settings['pygeo']
    ip = event.request.remote_addr
    geoip = gi.record_by_addr(ip)
    event.request.geoip = geoip
