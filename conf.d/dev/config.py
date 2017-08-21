# -*- coding: utf-8 -*-
import os

APP_ENV = "development"
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    MONGODB_SETTINGS = {
            'db': 'uop',
            'host': '172.28.20.124',
            'port': 27017,
            'username': 'uop',
            'password': 'uop',
            }
    CRP_URL = "http://172.28.32.32:8001/"
    CMDB_URL = "http://cmdb-dev.syswin.com/"

    UPLOAD_FOLDER = "/data/"
    #TODO:  move it to conf
    DISCONF_URL = 'http://172.28.11.111:8081'
    DISCONF_USER_INFO = {'name': 'admin', 'password': 'admin', 'remember': '0'}

configs = {
    'development': DevelopmentConfig,
}
