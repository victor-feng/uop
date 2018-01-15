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
    TESTING = True
    DEBUG = True
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
    CMDB2_URL = "http://cmdb2-test.syswin.com/"
    CMDB2_OPEN_USER = "uop"
    CMDB2_VIEWS = {
        "1": ("B7", u"工程 --> 物理机"),
        "2": ("B6", u"部门 --> 业务 --> 资源"),
        "3": ("B5", u"人 --> 部门 --> 工程"),
        "4": ("B4", u"资源 --> 环境 --> 机房"),
        "5": ("B3", u"资源 --> 机房"),
    }

    UPLOAD_FOLDER = "/data/"

configs = {
    'development': DevelopmentConfig,
}
