# -*- coding: utf-8 -*-
import os

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


class TestingConfig(BaseConfig):
    TESTING = True
    MONGODB_SETTINGS = {
            'db': 'uop',
            'host': '172.28.20.124',
            'port': 27017,
            'username': 'uop',
            'password': 'uop',
            }


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
