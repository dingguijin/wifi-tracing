import tornado.web
import tornado.httpserver

import json

import mysql

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        db = self.application.db
        if not db:
            self.application.db = mysql.Mysql() 
            db = self.application.db
        assert(db)
        db.open_session()
            
    def on_finish(self):
        db = self.application.db
        assert(db)
        db.close_session()

    def insert_calibration(self, d):
        db = self.application.db
        assert(db)
        db.insert_calibration(d)

class CalibrationHandler(BaseHandler):

    def post(self):
        print self.request.body
        cp = json.loads(self.request.body)
        if cp["calibration_value"] == -1:
            return
        self.insert_calibration(cp)

class Application(tornado.web.Application):

    def __init__(self):
        settings = {
            #"static_path" : os.path.join(os.path.dirname(__file__), "static"),
            #"upload_path" : os.path.join(os.path.dirname(__file__), "uphtml"),
            #"template_path" : os.path.join(os.path.dirname(__file__), "template"),
            #"cookie_secret" : "24oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            #"login_url" : "/login",
            # "xsrf_cookies": True,
            # "autoescape":None,
            "debug" : True
        }
        handlers = [
            (r"/calibration", CalibrationHandler),
	]
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = None
        
def start_web_service():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8999)
    loop = tornado.ioloop.IOLoop.instance()
    loop.start()

if __name__ == "__main__":
    start_web_service()
