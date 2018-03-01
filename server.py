# -*- coding: utf-8 -*-

import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
import os
import tornado.log


define('port', type=int, default=5000)
# deploy or debug
define('mode', default='debug')

# dev, test, prod
define('deploy', default='dev')
options.parse_command_line()
os.system('rm -rf config.py')
os.system('rm -rf config.pyc')
os.system('rm -rf conf')
os.system('ln -s conf.d/%s  conf '%(options.deploy))
os.system('ln -s conf/config.py  config.py')

from config import APP_ENV
from uop import create_app
from uop.log import logger_setting

def main():
    if options.mode.lower() == "debug":
        from tornado import autoreload
        autoreload.start()

    app = create_app(APP_ENV)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(options.port)
    logging.warn("[UOP] UOP is running on: localhost:%d", options.port)
    # set app log
    logger = logger_setting(app)
    fm = tornado.log.LogFormatter(
        fmt='[%(asctime)s]%(color)s[%(levelname)s]%(end_color)s[%(pathname)s %(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    tornado.log.enable_pretty_logging(logger=logger)
    logger.handlers[0].setFormatter(fm)

    IOLoop.instance().start()

if __name__ == '__main__':
    main()
