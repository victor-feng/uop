# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import threading
import logging

from flask import request
from flask_restful import reqparse, Api, Resource
from flask import current_app

from uop.dns import dns_blueprint
from uop.models import Deployment, ResourceModel
from uop.dns.errors import dns_errors
#from config import APP_ENV, configs
from api import Dns


#CPR_URL = configs[APP_ENV].CRP_URL
#CMDB_URL = configs[APP_ENV].CMDB_URL
#UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER

CPR_URL = current_app.config['CRP_URL']
CMDB_URL = current_app.config['CMDB_URL']
UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']

dns_api = Api(dns_blueprint, errors=dns_errors)
mu_lock = threading.Lock()


class DnsThread(threading.Thread, Dns):
    def __init__(self, env, domain):
        self.env = env
        self.domain = domain
        Dns.__init__(self, env)

    def run(self):
        global mu_lock
        if mu_lock.acquire():
            self.dns_add(self.env, self.domain)
            mu_lock.release()


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
            """
            message = {}
            my_dns = Dns(env)
            fetch_response = my_dns.fetch_file()
            if fetch_response['success']:
                my_dns.dns_add(env, domain)
                message['fetch_result'] = 'fetch is ok'

            copy_response = my_dns.copy_file()
            if copy_response['success']:
                message['copy_result'] = 'copy is ok'

            """
            dns_thread = DnsThread(env, domain)
            dns_thread.start()
            message = 'success'
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
                    "msg": message,
                }
            }
            return res, 200


class DnsQueryAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location='args')
        parser.add_argument('domain', type=str, location='args')

        args = parser.parse_args()

        env = args.env
        domain = args.domain

        my_dns = Dns(env)
        result = my_dns.config_query(name=domain)
        return result['error'], 200

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

