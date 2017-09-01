# -*- coding: utf-8 -*-

import requests
import json
import logging

from flask_restful import reqparse, Api, Resource
from flask import current_app

from uop.pool import pool_blueprint
from uop.pool.errors import pool_errors
from uop.models import ConfigureEnvModel 
from uop.util import get_CRP_url
from uop.log import Log
from config import APP_ENV, configs

pool_api = Api(pool_blueprint, errors=pool_errors)


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
