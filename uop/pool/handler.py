# -*- coding: utf-8 -*-

import requests
import json
import logging

from flask_restful import reqparse, Api, Resource
from flask import current_app

from uop.pool import pool_blueprint
from uop.pool.errors import pool_errors
from uop.models import ConfigureEnvModel,NetWorkConfig
from uop.util import get_CRP_url, get_network_used
from uop.log import Log
from config import APP_ENV, configs

pool_api = Api(pool_blueprint, errors=pool_errors)

class NetworkListAPI(Resource):

    @classmethod
    def get(cls):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('env', type=str,location="args")
            args = parser.parse_args()
            env_=args.env
            res = []
            CRP_URL = get_CRP_url(env_)
            headers = {'Content-Type': 'application/json'}
            res_list = []
            url_ = '%s%s'%(CRP_URL, 'api/openstack/network/list')
            result = requests.get(url_, headers=headers)
            if result.json().get('code') == 200:
                cur_res = result.json().get('result').get('res')
                for key, value in cur_res:
                    res.append({'id': key, 'name': value})
        except Exception as e:
            err_msg = e.message
            #NOTE: Wrong usage!!!!!!
            logging.error('list az statistics err: %s' % err_msg)
            logging.exception('list az statistics err: %s' , e.args)
            #Log.logger.error('list az statistics err: %s' % err_msg)
            ret = {
                "code": 400,
                "result": {
                    "msg": "failed",
                    "res": e.message
                }
            }
            return ret, 400
        else:
            ret = {
                "code": 400,
                "result": {
                    "msg": "success",
                    "res": res
                }
            }
            return ret, 200


class NetworksAPI(Resource):

    @classmethod
    def get(cls):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('env', type=str,location="args")
            args = parser.parse_args()
            env=args.env
            network_info={}
            res = []
            Networks=NetWorkConfig.objects.filter(env=env)
            for network in Networks:
                name=network.name
                vlan_id=network.vlan_id
                network_info[name]=vlan_id
                res.append(network_info)
        except Exception as e:
            err_msg = e.args
            logging.error('list az statistics err: %s' % err_msg)
            ret = {
                "code": 400,
                "result": {
                    "msg": "failed",
                    "res": err_msg
                }
            }
            return ret, 400
        else:
            ret = {
                "code": 400,
                "result": {
                    "msg": "success",
                    "res": res
                }
            }
            return ret, 200




class StatisticAPI(Resource):

    @classmethod
    def get(cls):
        try:
            ret = ConfigureEnvModel.objects.all()
            envs = [{'id': env.id, 'name': env.name } for env in ret]
            urls = [{'url': get_CRP_url(e.get('id')), 'id': e.get('id') } for e in envs ]   
            headers = {'Content-Type': 'application/json'}
            res_list = []
            for url in urls:
                logging.info('[UOP] Get url: %s', url)
                url_ = '%s%s'%(url.get('url'), 'api/az/uopStatistics')
                logging.info('[UOP] Get the whole url: %s', url_)
                result = requests.get(url_, headers=headers)
                if result.json().get('code') == 200:
                    logging.debug(url_ + ' '+json.dumps(headers))
                    cur_res = result.json().get('result').get('res')
                    res_list.append({url.get('id'): cur_res})
            res = {'result': {'res': []}, 'code' : 200}
            res['result']['res'] = res_list
        except Exception as e:
            err_msg = e.message
            #NOTE: Wrong usage!!!!!!
            logging.error('list az statistics err: %s' % err_msg)
            logging.exception('list az statistics err: %s' , e.args)
            #Log.logger.error('list az statistics err: %s' % err_msg)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            return res, 200


pool_api.add_resource(StatisticAPI, '/statistics')
pool_api.add_resource(NetworksAPI, '/networks')