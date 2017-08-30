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
from  config import DEV_CRP_URL, TEST_CRP_URL, PROD_CRP_URL


pool_api = Api(pool_blueprint, errors=pool_errors)


class StatisticAPI(Resource):

    @classmethod
    def get(cls):
        try:
            dev_url = '%s%s'%(DEV_CRP_URL, 'api/az/uopStatistics')
            test_url = '%s%s'%(TEST_CRP_URL, 'api/az/uopStatistics')
            prod_url = '%s%s'%(PROD_CRP_URL, 'api/az/uopStatistics')

            headers = {'Content-Type': 'application/json'}
            logging.debug(dev_url+' '+json.dumps(headers))
            # 获取div环境
            dev_result = requests.get(dev_url, headers=headers)
            dev_res = {}
            if dev_result.json().get('code')==200:
                dev_res = dev_result.json().get('result').get('res')
            # 获取test环境
            test_result = requests.get(test_url, headers=headers)
            test_res = {}
            if test_result.json().get('code')==200:
                test_res = test_result.json().get('result').get('res')
	    # 获取线上环境
            prod_result = requests.get(prod_url, headers=headers)
            prod_res = {}
            if prod_result.json().get('code')==200:
                prod_res = prod_result.json().get('result').get('res')

            res = {'result': {'res': []}, 'code' : 200}
            res['result']['res'].append({'dev' : dev_res})
            res['result']['res'].append({'prod' : prod_res})
            res['result']['res'].append({'test' : test_res})
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
