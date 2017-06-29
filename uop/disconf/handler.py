# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os
import werkzeug

from flask import request
from flask_restful import reqparse, Api, Resource
from config import APP_ENV, configs
from uop import models
from uop.disconf import disconf_blueprint
from uop.disconf.errors import disconf_errors

disconf_api = Api(disconf_blueprint, errors=disconf_errors)

DISCONF_URL = configs[APP_ENV].DISCONF_URL
SIGNIN = DISCONF_URL + '/api/account/signin'
SESSION = DISCONF_URL + '/api/account/session'
APP = DISCONF_URL + '/api/app'
FILETEXT = DISCONF_URL + '/api/web/config/filetext'
APP_LIST = DISCONF_URL + '/api/app/list'
ENV_LIST = DISCONF_URL + '/api/env/list'
VERSION_LIST = DISCONF_URL + '/api/web/config/versionlist'
CONFIG_LIST = DISCONF_URL + '/api/web/config/list'
CONFIG_SHOW = DISCONF_URL + '/api/web/config'
CONFIG_DEL = DISCONF_URL + '/api/web/config'
session = requests.Session()


def disconf_signin():
    user_info = {'name': 'admin', 'password': 'admin', 'remember': '1'}
    rep = requests.post(SIGNIN, data=user_info)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_session():
    user_info = {'name': 'admin', 'password': 'admin', 'remember': '0'}
    res = session.post(SIGNIN, data=user_info)
    ret_json = json.loads(res.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_app(app_name, desc):
    app_info = {'app': app_name, 'desc': desc, 'emails': ''}
    rep = session.post(APP, data=app_info)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_filetext(appId, envId, version, fileContent, fileName):
    filetext = {
        'appId': appId,
        'envId': envId,
        'version': version,
        'fileContent': fileContent,
        'fileName': fileName
    }
    rep = session.post(FILETEXT, data=filetext)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_filetext_update(config_id, filecontent):
    url = FILETEXT + '/' + config_id
    filetext = {
        'fileContent': filecontent
    }
    rep = session.put(url, data=filetext)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_filetext_delete(config_id):
    url = CONFIG_DEL + '/' + config_id
    rep = session.delete(url)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json



def disconf_app_list():
    rep = session.get(APP_LIST)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_app_id(app_name):
    app_id = None
    ret, msg = disconf_app_list()
    if not ret:
        return app_id, msg
    app_list = msg.get('page').get('result')
    for name in app_list:
        # name.get('name') is unicode
        if name.get('name') == app_name:
            # app_id is instance of int
            app_id = name.get('id')
            break
    return app_id, msg


def disconf_env_list():
    rep = session.get(ENV_LIST)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        return True, ret_json
    else:
        return False, ret_json


def disconf_env_id(env_name):
    env_id = None
    ret, msg = disconf_env_list()
    if not ret:
        return env_id, msg
    env_list = msg.get('page').get('result')
    if env_list:
        for env in env_list:
            if env.get('name') == env_name:
                env_id = env.get('id')
                break
    return env_id, msg


# def disconf_version_list(app_id, env_id):
#     url = ENV_LIST + '?appId=' + app_id + '&envId=' + env_id
#     rep = session.get(url)
#     ret_json = json.loads(rep.text)
#     result = ret_json.get('success')
#     if result == 'true':
#         vid = ret_json.get('page').get('result')[0].get('id')
#         version_id = str(vid)
#     else:
#         version_id = None
#     return version_id, ret_json


def disconf_version_list(app_id):
    url = VERSION_LIST + '?appId=' + app_id
    rep = session.get(url)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        result_list = ret_json.get('page').get('result')
        if result_list:
            version_id = ret_json.get('page').get('result')[0]
        else:
            version_id = None
    else:
        version_id = None
    return version_id, ret_json


def disconf_config_list(app_id, env_id, version):
    url = CONFIG_LIST + '?appId=' + app_id + '&envId=' + env_id + '&version=' + version + '&'
    rep = session.get(url)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        config_list = ret_json.get('page').get('result')
    else:
        config_list = []
    return config_list, ret_json


def disconf_config_show(config_id):
    url = CONFIG_SHOW + '/' + config_id
    rep = session.get(url)
    ret_json = json.loads(rep.text)
    result = ret_json.get('success')
    if result == 'true':
        config = ret_json.get('result')
    else:
        config = None
    return config, ret_json








class DisconfAPI(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('filename', type=str, location='json')
        parser.add_argument('filecontent', type=str, location='json')
        # parser.add_argument('version', type=str, location='json')
        parser.add_argument('res_id', type=str)
        args = parser.parse_args()

        res_id = args.get("res_id")
        # version = args.get('version')
        version = "1_0_0"
        fileName = args.get('filename')
        fileContent = args.get('filecontent')
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            code = 500
            res = "Failed to find the rsource. "
            ret = {
                "code": code,
                "result": {
                    "res": res + e.message,
                    "msg": ""
                }
            }
            return ret, code
        res_name = resource.resource_name
        ret, msg = disconf_session()
        if not ret:
            return msg, 200
        ret, msg = disconf_app(res_name, res_name + " config generated.")
        if not ret:
            return msg, 200

        app_id, msg = disconf_app_id(res_name)
        if app_id is None:
            return msg, 200
        env_id, msg = disconf_env_id('rd')

        ret, msg = disconf_filetext(app_id, env_id, version, fileContent, fileName)
        return msg, 200


    @classmethod
    def get(cls):
        configurations = []
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str, location='args')
        # parser.add_argument('env_id', type=str, location='args')

        args = parser.parse_args()
        res_id = args.res_id
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            code = 500
            res = "Failed to find the rsource. "
            ret = {
                "code": code,
                "result": {
                    "res": res + e.message,
                    "msg": ""
                }
            }
            return ret, code
        app_name = resource.resource_name

        ret, msg = disconf_session()
        if not ret:
            return msg, 200
        app_id, msg = disconf_app_id(app_name)
        if app_id is None:
            return msg, 200
        app_id = str(app_id)

        version_id, msg = disconf_version_list(app_id)
        if version_id is None:
            return msg, 200

        config_list, msg = disconf_config_list(app_id, '1', version_id)
        if config_list is None:
            return msg, 200
        config_value = dict()

        for conf in config_list:
            config, msg = disconf_config_show(str(conf.get('configId')))
            if config is not None:
                config_value['filename'] = config.get('key')
                config_value['filecontent'] = config.get('value')
                config_value['config_id'] = config.get('configId')
                configurations.append(config_value)
                config_value = {}
        ret = {
            'message': "Get configurations of " + app_name,
            'success': 'true',
            'config': configurations
        }

        return ret, 200


class DisconfItem(Resource):
    # @classmethod
    # def put(cls, config_id):
    #     parser = reqparse.RequestParser()
    #     parser.add_argument('filecontent', type=str, location='json')
    #     args = parser.parse_args()
    #     filecontent = args.get('filecontent')
    #
    #     ret, msg = disconf_session()
    #     if not ret:
    #         return msg, 200
    #
    #     ret, msg = disconf_filetext_update(config_id, filecontent)
    #     return msg, 200
    @classmethod
    def put(cls, res_id):
        parser = reqparse.RequestParser()
        parser.add_argument('filecontent', type=str, location='json')
        parser.add_argument('filename', type=str, location='json')
        args = parser.parse_args()
        filecontent = args.get('filecontent')
        filename = args.get('filename')
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            code = 500
            res = "Failed to find the rsource. "
            ret = {
                "code": code,
                "result": {
                    "res": res + e.message,
                    "msg": ""
                }
            }
            return ret, code

        app_name = resource.resource_name

        ret, msg = disconf_session()
        if not ret:
            return msg, 200
        app_id, msg = disconf_app_id(app_name)
        if app_id is None:
            return msg, 200
        app_id = str(app_id)
        version_id, msg = disconf_version_list(app_id)
        if version_id is None:
            return msg, 200

        config_list, msg = disconf_config_list(app_id, '1', version_id)
        if config_list is None:
            return msg, 200

        find = False
        for conf in config_list:
            config, msg = disconf_config_show(str(conf.get('configId')))
            if config is not None:
                if filename == config.get('key'):
                    ret, msg = disconf_filetext_update(str(config.get('configId')), filecontent)
                    find = True
                else:
                    ret, msg = disconf_filetext_delete(str(config.get('configId')))
        if not find:
            ret, msg = disconf_filetext(app_id, '1', version_id, filecontent, filename)

        return msg, 200


disconf_api.add_resource(DisconfAPI, '/')
# disconf_api.add_resource(DisconfItem, '/<string:config_id>/')
disconf_api.add_resource(DisconfItem, '/<string:res_id>/')
