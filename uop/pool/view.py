# -*- coding: utf-8 -*-

import requests
import json
from flask_restful import reqparse, Api, Resource
from uop.pool import pool_blueprint
from uop.pool.errors import pool_errors
from uop.models import ConfigureEnvModel,NetWorkConfig
from uop.util import get_CRP_url, get_network_used
from uop.log import Log


pool_api = Api(pool_blueprint, errors=pool_errors)


class NetworksAPI(Resource):

    @classmethod
    def get(cls):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('env', type=str,location="args")
            args = parser.parse_args()
            env=args.env
            res = []
            Networks=NetWorkConfig.objects.filter(env=env)
            for network in Networks:
                network_info={}
                name=network.name
                vlan_id=network.vlan_id
                sub_network = network.sub_network
                count,total_count=get_network_used(env, sub_network, vlan_id)
                rd_count=total_count-count
                if rd_count > 0:
                    network_info['name']=name
                    network_info['vlan_id']=vlan_id
                    network_info["total_count"]=total_count
                    network_info["count"]=count
                    network_info["rd_count"]=rd_count
                    res.append(network_info)
        except Exception as e:
            err_msg = e.args
            Log.logger.error('list az statistics err: %s' % err_msg)
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
                "code": 200,
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
            urls = [{'url': get_CRP_url(e.get('id')), 'env': e.get('id') } for e in envs ]
            headers = {'Content-Type': 'application/json'}
            res_list = []
            for url in urls:
                Log.logger.info('[UOP] Get url: %s', url)
                url_ = '%s%s'%(url.get('url'), 'api/az/uopStatistics')
                Log.logger.info('[UOP] Get the whole url: %s', url_)
                data_str = json.dumps({"env": url.get("env")})
                result = requests.get(url_, headers=headers, data=data_str)
                if result.json().get('code') == 200:
                    Log.logger.debug(url_ + ' '+json.dumps(headers))
                    cur_res = result.json().get('result').get('res')
                    res_list.append({url.get('env'): cur_res})
            res = {'result': {'res': []}, 'code' : 200}
            res['result']['res'] = res_list
        except Exception as e:
            err_msg = str(e.args)
            Log.logger.error('list az statistics err: %s' % err_msg)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": err_msg
                }
            }
            return res, 400
        else:
            return res, 200


pool_api.add_resource(StatisticAPI, '/statistics')
pool_api.add_resource(NetworksAPI, '/networks')
