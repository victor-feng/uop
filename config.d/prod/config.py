# -*- coding: utf-8 -*-
import os

APP_ENV = "prod"
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    DEBUG = False

class ProdConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    #MONGODB_SETTINGS = {
    #        'db': 'uop',
    #        'host': 'mongo-1',
    #        'port': 28010,
    #        'username': 'uop',
    #        'password': 'uop',
    #        }

    # Connect to mongo cluster. connections_list is invalid. 
    #MONGODB_SETTINGS = [
    #         {
    #        'db': 'uop',
    #        'host': 'mongo-1',
    #        'port': 28010,
    #        'username': 'uop',
    #        'password': 'uop',
    #        },
    #         {
    #        'db': 'uop',
    #        'host': 'mongo-2',
    #        'port': 28010,
    #        'username': 'uop',
    #        'password': 'uop',
    #        },
    #        {
    #        'db': 'uop',
    #        'host': 'mongo-3',
    #        'port': 28010,
    #        'username': 'uop',
    #        'password': 'uop',
    #        }
    #]


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
    'prod': ProdConfig,
}
