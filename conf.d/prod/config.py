# -*- coding: utf-8 -*-
import os

APP_ENV = "prod"
basedir = os.path.abspath(os.path.dirname(__file__))

DEV_CRP_URL = "http://crp-dev.syswin.com/"
TEST_CRP_URL = "http://crp.syswin.com/"
PROD_CRP_URL = "http://crp-dx.syswin.com/"


class BaseConfig:
    DEBUG = False

class ProdConfig(BaseConfig):
    # TESTING = True
    # DEBUG = True

    # Connect to mongo cluster. mongo_url is valid.
    MONGODB_SETTINGS = {
        'host': 'mongodb://uop:uop@mongo-1:28010,mongo-2:28010,mongo-3:28010/uop',
    }

    CRP_URL = {
        'dev': TEST_CRP_URL,
        'test': TEST_CRP_URL,
        'prep': PROD_CRP_URL,
        'prod': PROD_CRP_URL,
    }
    CMDB_URL = "http://cmdb.syswin.com/"
    CMDB2_URL = "http://cmdb2.syswin.com/"
    CMDB2_OPEN_USER = "uop"
    CMDB2_VIEWS = {
        "1": ("B7", u"工程 --> 物理机"),
        "2": ("B6", u"部门 --> 业务 --> 资源"),
        "3": ("B5", u"人 --> 部门 --> 工程"),
        "4": ("B4", u"资源 --> 环境 --> 机房"),
        # "5": ("B3", u"资源 --> 机房"),
    }
    UPLOAD_FOLDER = "/data/"


configs = {
    'prod': ProdConfig,
}
