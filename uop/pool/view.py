# -*- coding: utf-8 -*-

import requests
import json
from flask_restful import reqparse, Api, Resource
from flask import request
from uop.pool import pool_blueprint
from uop.pool.errors import pool_errors
from uop.models import ConfigureEnvModel,NetWorkConfig,ConfigureK8sModel,ConfOpenstackModel
from uop.util import get_CRP_url, get_network_used
from uop.log import Log
from uop.permission.handler import api_permission_control
from uop.util import response_data


pool_api = Api(pool_blueprint, errors=pool_errors)


class NetworksAPI(Resource):
    # @api_permission_control(request)
    @classmethod
    def get(cls):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('env', type=str,location="args")
            parser.add_argument('cloud', type=str, location="args")
            args = parser.parse_args()
            env=args.env
            cloud = args.cloud
            res = []
            Networks=NetWorkConfig.objects.filter(env=env,cloud=cloud)
            for network in Networks:
                network_info={}
                name=network.name
                vlan_id=network.vlan_id
                sub_network = network.sub_network
                if sub_network and vlan_id:
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
            Log.logger.error('get network info err: %s' % err_msg)
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
    # @api_permission_control(request)
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

class K8sNetworkApi(Resource):

    # @api_permission_control(request)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location="args")
        args = parser.parse_args()
        env = args.env
        data={}
        res_list=[]
        try:
            Networks = NetWorkConfig.objects.filter(env=env)
            for net in Networks:
                res={}
                networkName=net.networkName
                tenantName= net.tenantName
                if networkName and tenantName:
                    res["networkName"] = networkName
                    res["tenantName"] = tenantName
                    res_list.append(res)
            data["res_list"] = res_list
            code = 200
            msg = "Get k8s network info success"
        except Exception as e:
            code = 500
            data = "Error"
            msg = "Get k8s network info error %s" % str(e)
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

class GetK8sNamespace(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location="args")
        args = parser.parse_args()
        env = args.env
        data = {}
        res_list = []
        try:
            K8sInfos = ConfigureK8sModel.objects.filter(env=env)
            for info in K8sInfos:
                res = {}
                namespace_name = info.namespace_name
                if namespace_name:
                    res["namespace_name"] = namespace_name
                    res_list.append(res)
            data["res_list"] = res_list
            code = 200
            msg = "Get k8s namespace info info success"
        except Exception as e:
            code = 500
            data = "Error"
            msg = "Get k8s namespace info error %s" % str(e)
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

class GetImageFlavor(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location="args")
        parser.add_argument('cloud', type=str, location="args")
        parser.add_argument('resource_type', type=str, location="args")
        args = parser.parse_args()
        Log.logger.info("11111111111111111111111111--{}".format(args))
        env = args.env
        cloud = args.cloud
        resource_type = args.resource_type
        Log.logger.info("222222222222222222222222222222222 {}--{}--{}".format(env,cloud,resource_type))
        data = {}
        image_list = []
        flavor_list = []
        try:
            opsk_images = ConfOpenstackModel.objects.filter(cloud=cloud,env=env,image_type=resource_type)
            opsk_flavors = ConfOpenstackModel.objects.filter(cloud=cloud, env=env, flavor_type=resource_type)
            Log.logger.info("333333333333333333333333333333333333333333")
            for image in opsk_images:
                image_info = {}
                image_info["image_name"] = image.image_name
                image_info["image_id"] = image.image_id
                image_list.append(image_info)
            Log.logger.info("4444444444444444444444444444444444444444444")
            for flavor in opsk_flavors:
                flavor_info = {}
                flavor_info["flavor_id"] = flavor.flavor_id
                flavor_info["flavor_name"] = flavor.flavor_name
                flavor_list.append(flavor_list)
            Log.logger.info("5555555555555555555555555555555555555555555555555")
            data["flvor_list"] = flavor_list
            data["image_list"] = image_list
            code = 200
            msg = "Get openstack image flavor success"
        except Exception as e:
            code = 500
            data = "Error"
            msg = "Get openstack image flavor info error %s" % str(e)
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

















pool_api.add_resource(StatisticAPI, '/statistics')
pool_api.add_resource(NetworksAPI, '/networks')
pool_api.add_resource(K8sNetworkApi, '/k8s/network')
pool_api.add_resource(GetK8sNamespace, '/k8s/getnamespace')
pool_api.add_resource(GetImageFlavor, '/getimgflavors')
