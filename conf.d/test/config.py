# -*- coding: utf-8 -*-
import os

APP_ENV = "testing"
basedir = os.path.abspath(os.path.dirname(__file__))

DEV_CRP_URL = "http://172.28.32.32:8001/"
TEST_CRP_URL = "http://172.28.32.32:8001/"
PROD_CRP_URL = "http://172.28.32.32:8001/"


class BaseConfig:
    DEBUG = False

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True

    # Connect to mongo cluster. mongo_url is valid.
    MONGODB_SETTINGS = {
        'host': 'mongodb://uop:uop@mongo-1:28010,mongo-2:28010,mongo-3:28010/uop',
    }


    CRP_URL = "http://crp-test.syswin.com/"
    CMDB_URL = "http://cmdb-test.syswin.com/"

    UPLOAD_FOLDER = "/data/"
    #TODO:  move it to conf
    DISCONF_URL = 'http://172.28.11.111:8081'
    DISCONF_USER_INFO = {'name': 'admin', 'password': 'admin', 'remember': '0'}


configs = {
    'testing': TestingConfig,
}
