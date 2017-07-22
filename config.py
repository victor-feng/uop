# -*- coding: utf-8 -*-
import os

# APP_ENV = "default"
APP_ENV = "testing"
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    DEBUG = False


#NOTE:TODO? used?
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'xcloud',
        'host': 'develop.mongodb.db',
        'port': 27017,
        'username': 'xcloud',
        'password': 'xcloud'
    }
    CRP_URL = "http://172.28.32.32:8001/"
    CMDB_URL = "http://cmdb-test.syswin.com/"
    UPLOAD_FOLDER = "/tmp/"

class TestingConfig(BaseConfig):
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

    UPLOAD_FOLDER = "/tmp/"
    #TODO:  move it to conf
    DISCONF_URL = 'http://172.28.11.111:8081'


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
