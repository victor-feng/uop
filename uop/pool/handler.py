# -*- coding: utf-8 -*-

import requests
import json
import logging

from flask_restful import reqparse, Api, Resource
from flask import current_app

from uop.pool import pool_blueprint
from uop.pool.errors import pool_errors
#from uop.log import Log
#from config import APP_ENV, configs

pool_api = Api(pool_blueprint, errors=pool_errors)


class StatisticAPI(Resource):

    @classmethod
    def get(cls):
        try:
            url = current_app.config['CRP_URL']+'api/az/uopStatistics'
            #url = CRP_URL+'api/az/statistics'

            headers = {'Content-Type': 'application/json'}
            logging.debug(url+' '+json.dumps(headers))
            #Log.logger.debug(url+' '+json.dumps(headers))
            logging.debug(url+' '+json.dumps(headers))
    
            result = requests.get(url, headers=headers)
            res = result.json()
        except Exception as e:
            err_msg = e.message
            logging.error('list az statistics err: %s' % err_msg)
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
