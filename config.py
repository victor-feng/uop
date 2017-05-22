# -*- coding: utf-8 -*-
import os

APP_ENV = "default"
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'xcloud',
        'host': 'develop.mongodb.db',
        'port': 27017,
        'username': 'xcloud',
        'password': 'xcloud'
    }
    CRP_URL = "http://172.28.20.124:8000/"

class TestingConfig(BaseConfig):
    TESTING = True
    MONGODB_SETTINGS = {
            'db': 'uop',
            'host': '172.28.20.124',
            'port': 27017,
            'username': 'uop',
            'password': 'uop',
            }
    CRP_URL = "http://172.28.20.124:8000/"


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
