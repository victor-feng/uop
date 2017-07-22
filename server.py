# -*- coding: utf-8 -*-

import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options

from uop import create_app
from config import APP_ENV

if __name__ == '__main__':
    #NOTE:
    options.parse_command_line()

    logging.info('[UOP] come into main')

    app = create_app(APP_ENV)
    #app.run(host='0.0.0.0', debug=True)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start()
