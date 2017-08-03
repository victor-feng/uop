# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import logging
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
            app_name = resource.ins_name
            ret = disconf_add_app_config_api_content(app_name=app_name, filename=fileName, filecontent=fileContent)

            code = 200
            res = 'Disconf Success.'
            message = ret
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
        except Exception as e:
            logging.exception("[UOP] Disconf faild, Exception: %s", e.args)

        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": message,
            }
        }
        return ret, code


class DisconfItem(Resource):
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
            app_name = resource.resource_name
            ret = disconf_add_app_config_api_content(app_name=app_name, filename=filename, filecontent=filecontent)

            code = 200
            res = "Disconf put success."
            message = ret
        except Exception as e:
            code = 500
            res = "Disconf put error."
            message = e.message
        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": message
            }
        }
        return ret, 200


disconf_api.add_resource(DisconfAPI, '/')
# disconf_api.add_resource(DisconfItem, '/<string:config_id>/')
disconf_api.add_resource(DisconfItem, '/<string:res_id>/')
