# -*- coding: utf-8 -*-
import os

APP_ENV = "development"
basedir = os.path.abspath(os.path.dirname(__file__))

DEV_CRP_URL = "http://172.28.32.32:8001/"
TEST_CRP_URL = "http://172.28.32.32:8001/"
PROD_CRP_URL = "http://172.28.32.32:8001/"



class BaseConfig:
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    # TESTING = True
    # DEBUG = True
    MONGODB_SETTINGS = {
            'db': 'uop',
            'host': '172.28.20.124',
            'port': 27017,
            'username': 'uop',
            'password': 'uop',
            }
    CRP_URL = {
        'dev': DEV_CRP_URL,
        'test': TEST_CRP_URL,
        'prod': PROD_CRP_URL,
    }
    CMDB_URL = "http://cmdb-dev.syswin.com/"

    UPLOAD_FOLDER = "/data/"

configs = {
    'development': DevelopmentConfig,
}
