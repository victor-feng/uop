# -*- coding: utf-8 -*-

import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options

define('port', type=int, default=5000)

from uop import create_app
from config import APP_ENV

def main():
    options.parse_command_line()

    app = create_app(APP_ENV)
    # app.run(host='0.0.0.0', debug=True)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(options.port)
    logging.warn("[MPC] MPC is running on: localhost:%d", options.port)
    IOLoop.instance().start()

if __name__ == '__main__':
    main()
