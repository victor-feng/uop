# -*- coding: utf-8 -*-
import re
import json
from flask_restful import reqparse, Api, Resource, fields
import requests
from flask import request
from uop.configure import configure_blueprint
from uop.configure.handler import fuzzyfinder
from uop.models import ConfigureEnvModel
from uop.models import ConfigureNginxModel
from uop.models import ConfigureDisconfModel
from uop.models import NetWorkConfig,ConfigureK8sModel
from uop.util import get_CRP_url,response_data
from uop.log import Log
from uop.permission.handler import api_permission_control

configure_api = Api(configure_blueprint)


class ConfigureEnv(Resource):
    # @api_permission_control(request)
    @classmethod
    def get(cls):
        ret = ConfigureEnvModel.objects.all()
        envs = []
        for env in ret:
            envs.append(dict(id=env.id,
                             name=env.name))
        res = {
            'code': 200,
            'result': {
                'res': envs,
                'msg': u'请求成功'
            }
        }
        return res


class Configure(Resource):
    # @api_permission_control(request)
    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        args = parser.parse_args()
        env = args.env if args.env else 'dev'
        category = args.category
        Log.logger.info("[UOP] Get configs, env:%s, category: %s", env, category)
        envs = []
        # nets = []
        if category == 'nginx':
            ret = ConfigureNginxModel.objects.filter(env=env)
            for env in ret:
                envs.append(dict(id=env.id,
                                 name=env.name,
                                 ip=env.ip))
        elif category in ['network','k8s_network']:
            ret = NetWorkConfig.objects.filter(env=env)
            for net in ret:
                envs.append(dict(id=net.id,
                                 name=net.name,
                                 sub_network=net.sub_network,
                                 vlan_id=net.vlan_id,
                                 tenantName=net.tenantName,
                                 networkName=net.networkName))
        elif category == 'namespace':
            ret = NetWorkConfig.objects.filter(env=env)
            for net in ret:
                envs.append(dict(id=net.id,
                                 namespace=net.namespace,
                                ))

        else:  # disconf
            ret = ConfigureDisconfModel.objects.filter(env=env)
            for env in ret:
                envs.append(dict(id=env.id,
                                 name=env.name,
                                 username=env.username,
                                 password=env.password,
                                 ip=env.ip,
                                 url=env.url))
        res = {
            'code': 200,
            'result': {
                'res': envs,
                'msg': u'请求成功'
            }
        }
        return res

    # @api_permission_control(request)
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('ip', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('sub_network', type=str)
        parser.add_argument('vlan_id', type=str)
        parser.add_argument('networkName', type=str)
        parser.add_argument('tenantName', type=str)
        parser.add_argument('namespace', type=str)
        args = parser.parse_args()
        env = args.env if args.env else 'dev'
        url = args.url if args.url else ''
        ip = args.ip if args.ip else ''
        name = args.name if args.name else ''
        username = args.username if args.username else 'dev'
        password = args.password if args.password else 'dev'
        category = args.category if args.category else 'nginx'
        sub_network = args.sub_network if args.sub_network else ''
        vlan_id = args.vlan_id if args.vlan_id else ''
        networkName = args.networkName if args.networkName else ''
        tenantName = args.tenantName if args.tenantName else ''
        namespace = args.namespace if args.namespace else ''
        Log.logger.info("[UOP] Create configs, env:%s, category: %s", env, category)
        import uuid
        id = str(uuid.uuid1())
        if category == 'nginx':
            ret = ConfigureNginxModel(env=env,
                                      ip=ip,
                                      name=name,
                                      id=id).save()
        elif category in ['network','k8s_network']:
            ret = NetWorkConfig(env=env,
                                name=name,
                                sub_network=sub_network,
                                vlan_id=vlan_id,
                                tenantName=tenantName,
                                networkName=networkName,
                                id=id).save()
        elif category == "namespace":
            ret = ConfigureK8sModel(
                id = id,
                env = env,
                namespace = namespace,
            ).save()
        else:
            ret = ConfigureDisconfModel(env=env,
                                        url=url,
                                        ip=ip,
                                        name=name,
                                        username=username,
                                        password=password,
                                        id=id).save()
        res = {
            'code': 200,
            'result': {
                'res': id,
                'msg': u'请求成功'
            }
        }
        return res

    # @api_permission_control(request)
    @classmethod
    def put(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('ip', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('id', type=str)
        parser.add_argument('sub_network', type=str)
        parser.add_argument('vlan_id', type=str)
        parser.add_argument('networkName', type=str)
        parser.add_argument('tenantName', type=str)
        parser.add_argument('namespace', type=str)
        args = parser.parse_args()
        category = parser.parse_args()
        env = args.env if args.env else 'dev'
        id = args.id if args.id else ''
        url = args.url if args.url else ''
        ip = args.ip if args.ip else ''
        name = args.name if args.name else ''
        category = args.category if args.category else 'nginx'
        username = args.username if args.username else ''
        password = args.password if args.password else ''
        sub_network = args.sub_network if args.sub_network else ''
        vlan_id = args.vlan_id.strip() if args.vlan_id else ''
        networkName = args.networkName if args.networkName else ''
        tenantName = args.tenantName if args.tenantName else ''
        namespace = args.namespace if args.namespace else ''
        Log.logger.info("[UOP] Modify configs, env:%s, category: %s", env, category)

        if category == 'nginx':
            ret = ConfigureNginxModel.objects(id=id)
            ret.update(name=name, ip=ip)
        elif category in ['network','k8s_network']:
            ret = NetWorkConfig.objects(id=id)
            ret.update(name=name, sub_network=sub_network, vlan_id=vlan_id,networkName=networkName,tenantName=tenantName)
        elif category == "namespace":
            ret = ConfigureK8sModel.objects(id = id)
            ret.update(id=id,env=env,namespace=namespace)
        else:
            ret = ConfigureDisconfModel.objects(id=id)
            ret.update(name=name, url=url, ip=ip, username=username, password=password)

        res = {
            'code': 200,
            'result': {
                'msg': u'请求成功'
            }
        }
        return res

    # @api_permission_control(request)
    @classmethod
    def delete(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        parser.add_argument('id', type=str)
        args = parser.parse_args()
        category = parser.parse_args()
        env = args.env if args.env else 'dev'
        category = args.category if args.category else 'nginx'
        id = args.id if args.id else -1
        Log.logger.info("[UOP] Delete configs, env:%s, category: %s, id: %s", env, category, id)

        if category == 'nginx':
            ret = ConfigureNginxModel.objects.filter(id=id)
        elif category  in ['network','k8s_network']:
            ret = NetWorkConfig.objects.filter(id=id)
        elif category == "namespace":
            ret = ConfigureK8sModel.objects.filter(id=id)
        else:
            ret = ConfigureDisconfModel.objects.filter(id=id)
        if len(ret):
            ret.delete()
        else:
            Log.logger.info("[UOP] Do not found the item, id:%s", id)

        res = {
            'code': 200,
            'result': {
                'msg': u'请求成功'
            }
        }
        return res


class ConfigureNetwork(Resource):
    # @api_permission_control(request)
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('keywords', type=str)
            parser.add_argument('env', type=str)
            args = parser.parse_args()
            keywords = args.keywords
            env_ = args.env
            network_list = []
            CRP_URL = get_CRP_url(env_)
            headers = {'Content-Type': 'application/json'}
            url_ = '%s%s' % (CRP_URL, 'api/openstack/network/list')
            result = requests.get(url_, headers=headers)
            networks = result.json().get('result').get('res')
            if keywords:
                fuzzy_res = {}
                network_names = fuzzyfinder(keywords, networks.keys())
                for name in network_names:
                    fuzzy_res[name] = networks[name]
                networks = fuzzy_res
            for name, info in networks.items():
                network_info = {}
                network_info["vlan_name"] = name
                network_info["vlan_id"] = info[0]
                network_info["subnets"] = info[1]
                network_list.append(network_info)
        except Exception as e:
            err_msg = e.args
            Log.logger.error('Uop get network list err: %s' % err_msg)
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
                    "res": network_list
                }
            }
            return ret, 200

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
            url=get_CRP_url(env)+'api/openstack/k8s/network?env=%s' %env
            result = requests.get(url)
            code=result.json().get('code')
            if code == 200:
                result_list= result.json().get('result')['data']['res_list']
                for r in result_list:
                    res={}
                    res["networkName"] = r.get("networkName")
                    res["tenantName"] = r.get("tenantName")
                    res_list.append(res)
            msg = result.json().get('result')["msg"]
            data["res_list"] = res_list
            code = code
        except Exception as e:
            code = 500
            data = "Error"
            msg = "Get k8s network info error %s" % str(e)
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

class K8sNamespaceManage(Resource):

    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('namespace_name', type=str, location="json")
        parser.add_argument('config_map_name', type=str, location="json")
        parser.add_argument('config_map_infp', type=str, location="json")
        parser.add_argument('env', type=str, location="json")
        args = parser.parse_args()
        env = args.env
        namespace_name = args.namespace_name
        config_map_name = args.config_map_name
        config_map_info = args.config_map_info
        data={}
        try:
            url = get_CRP_url(env) + 'api/openstack/k8s/namespace'
            data["namespace_name"] = namespace_name
            if config_map_name:
                config_map_data = {}
                data["namespace_name"] = namespace_name
                config_map_data["filebeat.yml"] = config_map_info
                data["config_map_data"] = config_map_data
            headers = {'Content-Type': 'application/json'}
            data_str = json.dumps(data)
            result = requests.post(url=url,data=data_str,headers=headers)
            code = result.json().get('code')
            msg = result.json().get('result')["msg"]
            data = result.json().get('result')["data"]
        except Exception as e:
            code = 500
            data = "Error"
            msg = "create k8s namespace error {e}".format(e=str(e))
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location="args")
        args = parser.parse_args()
        env = args.env
        data = {}
        res_list = []
        try:
            url = get_CRP_url(env) + 'api/openstack/k8s/namespace'
            result = requests.get(url)
            code = result.json().get('code')
            if code == 200:
                res_list = result.json().get('result')['data']['res_list']
            msg = result.json().get('result')['msg']
            data["res_list"] = res_list
        except Exception as e:
            code = 500
            data = "Error"
            msg = "Get k8s namespace info error {e}".format(e=str(e))
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code





configure_api.add_resource(ConfigureEnv, '/env')
configure_api.add_resource(Configure, '/')
configure_api.add_resource(ConfigureNetwork, '/network')
configure_api.add_resource(K8sNetworkApi, '/k8s/networks')
configure_api.add_resource(K8sNamespaceManage, '/k8s/namespace')
