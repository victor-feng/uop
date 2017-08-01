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
from uop.disconf.disconf_api import *


disconf_api = Api(disconf_blueprint, errors=disconf_errors)


class DisconfAPI(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('filename', type=str, location='json')
        parser.add_argument('filecontent', type=str, location='json')
        # parser.add_argument('version', type=str, location='json')
        parser.add_argument('res_id', type=str, location='json')
        parser.add_argument('ins_name', type=str, location='json')
        args = parser.parse_args()

        res_id = args.get("res_id")
        # version = args.get('version')
        version = "1_0_0"
        fileName = args.get('filename')
        fileContent = args.get('filecontent')

        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
            app_name = ins_info.ins_name
            app_desc = '{res_name} config generated.'.format(res_name=app_name)
            disconf_app(app_name, app_desc)
            app_id = disconf_app_id(app_name)
            env_id = disconf_env_id('rd')
            ret = disconf_filetext(app_id, env_id, version, fileContent, fileName)


            code = 200
            res = 'Disconf Success.'
            message = message
        except ServerError as e:
            code = 500
            res = "Disconf Failed."
            message = e.message

        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": message
            }
        }
        return ret, code



    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str, location='args')
        #parser.add_argument('env_id', type=str, location='args')

        args = parser.parse_args()
        res_id = args.res_id
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
            compute_list = resource.compute_list
            print compute_list
            message = []
            for ins_info in resource.compute_list:
                if ins_info is not None:
                    result = {}
                    app_name = getattr(ins_info,'ins_name')
                    app_id = disconf_app_id(app_name=app_name)
                    env_id = disconf_env_id(env_name='rd')
                    version_id = disconf_version_list(app_id=app_id)
                    config_id_list = disconf_config_id_list(app_id=app_id, env_id=env_id, version=version_id)

                    configurations = []
                    for config_id in config_id_list:
                        config = disconf_config_show(config_id)
                        config_value = {}
                        if config is not None:
                            config_value['filename'] = config.get('key')
                            config_value['filecontent'] = config.get('value')
                            config_value['config_id'] = config.get('configId')
                            configurations.append(config_value)
                    result[app_name] = configurations
                    message.append(result)
            code = 200
            res = "Configurations Success."
        except ServerError as e:
            code = 500
            res = "Configurations Failed."
            message = e.message

        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": message,
            }
        }
        return ret, code


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
