# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os

from flask import request
from flask_restful import reqparse, Api, Resource
from uop.dns import dns_blueprint
from uop.models import Deployment, ResourceModel
from uop.dns.errors import dns_errors
from config import APP_ENV, configs
from api import ServerError, AnsibleConnect, Dns


CPR_URL = configs[APP_ENV].CRP_URL
CMDB_URL = configs[APP_ENV].CMDB_URL
UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER

dns_api = Api(dns_blueprint, errors=dns_errors)


class DnsAddAPI(Resource):
    """
    添加dns操作
    """

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location='json')
        parser.add_argument('domain', type=str, location='json')

        args = parser.parse_args()

        env = args.env
        domain = args.domain
        try:
            connect_to_ansible = AnsibleConnect(env)
            fetch_response = connect_to_ansible.fetch_file()
            if fetch_response['success']:
                Dns.dns_add(env, domain)
                fetch_result = 'fetch is ok'
            else:
                raise ServerError('ansible fetch is error')

            copy_response = connect_to_ansible.copy_file()
            if copy_response['success']:
                copy_result = 'copy is ok'
            else:
                raise ServerError('ansible copy is error')
        except Exception as e:
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "res": "success",
                    "msg": {"fetch": fetch_result, "copy": copy_result},
                }
            }
            return res, 200


class DnsQueryAPI(Resource):

    def put(self, deploy_id):
        pass

    def delete(self, deploy_id):
        res_code = 204
        deploys = Deployment.objects(deploy_id=deploy_id)
        if deploys.count() > 0:
            deploys.delete()
        else:
            res_code = 404
        return "", res_code

dns_api.add_resource(DnsAddAPI, '/dns_add')
dns_api.add_resource(DnsQueryAPI, '/dns_query')

