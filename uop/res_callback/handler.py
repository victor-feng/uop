# -*- coding: utf-8 -*-

import json
import uuid
import copy
import requests
import logging

from flask import request
from flask_restful import reqparse, Api, Resource
from flask import current_app

from uop.res_callback import res_callback_blueprint
from uop.models import User, ResourceModel
from uop.res_callback.errors import res_callback_errors
from config import APP_ENV, configs
from transitions import Machine
#from uop.log import Log


res_callback_api = Api(res_callback_blueprint, errors=res_callback_errors)


#CMDB_URL = current_app.config['CMDB_URL']
#CMDB_URL = configs[APP_ENV].CMDB_URL
#CMDB_RESTAPI_URL = CMDB_URL+'cmdb/api/'
#CMDB_REPO_URL = CMDB_RESTAPI_URL+'repo/'
#CMDB_ITEM_PROPERTY_LIST_URL = CMDB_RESTAPI_URL+'property_list/'
#CMDB_ITEM_URL = CMDB_RESTAPI_URL+'cmdb/item/'
#CMDB_REPO_ITEM_CONDITION_GET_URL = CMDB_RESTAPI_URL+'repo_detail/'


# Define CallBack JSON Format
items_sequence_list_config = [
    {
        'deploy_instance':
            {
                'container':
                    [
                        {
                            'app_cluster':
                                [
                                    {
                                        'instance':
                                            {
                                                'app_instance'
                                            }
                                     }
                                ]
                        }
                    ],
                'db_info':
                    {
                        'mysql':
                            {
                                'mysql_cluster':
                                    [
                                        {
                                            'instance':
                                                {
                                                    'mysql_instance'
                                                }
                                        }
                                    ],
                            },
                        'mongodb':
                            {
                                'mongodb_cluster':
                                    [
                                        {
                                            'instance':
                                                {
                                                    'mongodb_instance'
                                                }
                                        }
                                    ],
                            },
                        'redis':
                            {
                                'redis_cluster':
                                    [
                                        {
                                            'instance':
                                                {
                                                    'redis_instance'
                                                }
                                        }
                                    ]
                            }
                    }
            }
    }]


# Define CMDB Item Property p_code to CallBack JSON Property Mapper
property_json_mapper_config = {
    'deploy_instance': {
        'name': 'resource_name',
        'deploy_instance_id': 'resource_id',
        'project_pople': 'username',
        'project_dep': 'department',
        'create_time': 'created_time',
        'reservation_status': 'status',
        'deploy_status': 'deploy_status',
    },
    'app_cluster': {
        'name': 'cluster_name',
        'project_domain': 'domain'
    },
    'app_instance': {
        'name': 'container_name',
        'ip': 'ip',
        'ip_address': 'ip',
        'cpu_count': 'cpu',
        'memory_count': 'memory',
        'username': 'username',
        'password': 'password',
        'image_addr': 'image_addr',
        'physical_server': 'physical_server'
    },
    'docker': {
        'name': 'container_name',
        'ip_address': 'ip',
        'cpu_count': 'cpu',
        'memory_count': 'memory',
        'username': 'username',
        'password': 'password',
        'image_addr': 'image_addr',
        'physical_server': 'physical_server'
    },
    'mysql_cluster': {
        'name': 'name',
        "username": "username",
        "password": "password",
        "port": "port",
        "mysql_cluster_wvip": "wvip",
        "mysql_cluster_rvip": "rvip",
        "ins_id": "ins_id"
    },
    'mysql_instance': {
        'name': 'name',
        "mysql_username": "username",
        "mysql_password": "password",
        "dbtype": "dbtype",
        'ip_address': 'ip',
        "port": "port",
        'cpu_count': 'cpu',
        'memory_count': 'memory',
        'physical_server': 'physical_server'
    },
    'mongodb_cluster': {
        'name': 'name',
        "username": "username",
        "password": "password",
        "port": "port",
        "mongodb_cluster_ip1": "vip1",
        "mongodb_cluster_ip2": "vip2",
        "mongodb_cluster_ip3": "vip3",
        "ins_id": "ins_id"
    },
    'mongodb_instance': {
        'name': 'name',
        "username": "username",
        "password": "password",
        "dbtype": "dbtype",
        'ip_address': 'ip',
        "port": "port",
        'cpu_count': 'cpu',
        'memory_count': 'memory',
        'physical_server': 'physical_server'
    },
    'redis_cluster': {
        'name': 'name',
        "username": "username",
        "password": "password",
        "port": "port",
        "redis_cluster_vip": "vip",
        "ins_id": "ins_id"
    },
    'redis_instance': {
        'name': 'name',
        "username": "username",
        "password": "password",
        "dbtype": "dbtype",
        'ip_address': 'ip',
        "port": "port",
        'cpu_count': 'cpu',
        'memory_count': 'memory',
        'physical_server': 'physical_server'
    },
    'virtual_server': {
        'name': 'name',
        'ip_address': 'ip',
        'cpu_count': 'cpu',
        'memory_count': 'memory',
        'username': 'username',
        'password': 'password',
        'physical_server': 'physical_server'
    },
}


# Transition state Log debug decorator
def transition_state_logger(func):
    def wrapper(self, *args, **kwargs):
        logging.debug("Transition state is turned in " + self.state)
        ret = func(self, *args, **kwargs)
        logging.debug("Transition state is turned out " + self.state)
        return ret
    return wrapper


class ResourceProviderTransitions(object):
    # Define some states.
    states = ['init', 'stop',
              'deploy_instance',
              'app_cluster', 'app_instance',
              'mysql_cluster', 'mysql_instance',
              'mongodb_cluster', 'mongodb_instance',
              'redis_cluster', 'redis_instance',
              'docker', 'virtual_server']

    # Define transitions.
    transitions = [
        {'trigger': 'stop', 'source': '*', 'dest': 'stop', 'after': 'do_stop'},
        {'trigger': 'deploy_instance', 'source': 'init', 'dest': 'deploy_instance', 'after': 'do_deploy_instance'},
        {'trigger': 'app_cluster', 'source': ['deploy_instance', 'docker', 'virtual_server'], 'dest': 'app_cluster', 'after': 'do_app_cluster'},
        {'trigger': 'app_instance', 'source': 'app_cluster', 'dest': 'app_instance', 'after': 'do_app_instance'},
        {'trigger': 'app_instance', 'source': 'docker', 'dest': 'app_instance', 'after': 'do_app_instance'},
        {'trigger': 'mysql_cluster', 'source': ['deploy_instance', 'docker', 'virtual_server'], 'dest': 'mysql_cluster', 'after': 'do_mysql_cluster'},
        {'trigger': 'mysql_instance', 'source': 'mysql_cluster', 'dest': 'mysql_instance', 'after': 'do_mysql_instance'},
        {'trigger': 'mysql_instance', 'source': 'virtual_server', 'dest': 'mysql_instance', 'after': 'do_mysql_instance'},
        {'trigger': 'mongodb_cluster', 'source': ['deploy_instance', 'docker', 'virtual_server'], 'dest': 'mongodb_cluster', 'after': 'do_mongodb_cluster'},
        {'trigger': 'mongodb_instance', 'source': 'mongodb_cluster', 'dest': 'mongodb_instance', 'after': 'do_mongodb_instance'},
        {'trigger': 'mongodb_instance', 'source': 'virtual_server', 'dest': 'mongodb_instance', 'after': 'do_mongodb_instance'},
        {'trigger': 'redis_cluster', 'source': ['deploy_instance', 'docker', 'virtual_server'], 'dest': 'redis_cluster', 'after': 'do_redis_cluster'},
        {'trigger': 'redis_instance', 'source': 'redis_cluster', 'dest': 'redis_instance', 'after': 'do_redis_instance'},
        {'trigger': 'redis_instance', 'source': 'virtual_server', 'dest': 'redis_instance', 'after': 'do_redis_instance'},
        {'trigger': 'docker', 'source': 'app_instance', 'dest': 'docker', 'after': 'do_docker'},
        {'trigger': 'virtual_server', 'source': ['mysql_instance', 'mongodb_instance', 'redis_instance'], 'dest': 'virtual_server', 'after': 'do_virtual_server'}
    ]

    def __init__(self, property_mappers_list):
        """
        property_mappers_list = [
            {
                'deploy_instance': {
                     'name': '部署实例1',
                     'resource_id': '资源ID'
                 }
             },
            {
                'app_cluster': {
                     'name': '应用集群1',
                     'domain': 'checkin.syswin.com'
                 }
             }
        ]
        """
        # Initialize the variable
        self.property_mappers_list = copy.deepcopy(property_mappers_list)
        self.property_mappers_list.reverse()
        # 刚刚处理过的节点，可能为存在引用关系的父节点
        self.pre_property_mapper = {}
        # 待处理的节点
        self.property_mapper = {}

        # self.pcode_mapper 仅记录最近一次更新的 pcode 数据，因此集群需要按如下顺序构造property_mappers_list
        # 第一个集群 -> 第一个集群的实例1 -> …… -> 第一个集群的实例n -> 第二个集群 -> 第二个集群的实例1 -> ……
        self.pcode_mapper = {}

        # Initialize the state machine
        self.machine = Machine(model=self,
                               states=ResourceProviderTransitions.states,
                               transitions=ResourceProviderTransitions.transitions,
                               initial='init')

    def preload_property_mapper(self):
        if len(self.property_mappers_list) != 0:
            if len(self.pre_property_mapper) == 0:
                self.pre_property_mapper = self.property_mapper
            if len(self.pre_property_mapper) != 0 and len(self.property_mapper) != 0 \
                    and (self.pre_property_mapper.keys()[0] != self.property_mapper.keys()[0]):
                self.pre_property_mapper = self.property_mapper
            self.property_mapper = self.property_mappers_list.pop()
        else:
            self.pre_property_mapper = {}
            self.property_mapper = {}

    def tick_announce(self):
        self.preload_property_mapper()
        if len(self.property_mapper) != 0:
            item_id = self.property_mapper.keys()[0]
            func = getattr(self, item_id, None)
            if not func:
                raise NotImplementedError("Unexpected item_id=%s" % item_id)
            logging.debug('Trigger is %s', item_id)
            func()
        else:
            self.stop()

    def transit_item_property_list(self, item_id):
        repo_item = {}
        transited_property_list = []
        try:
            CMDB_URL = current_app.config['CMDB_URL'] 
            CMDB_ITEM_PROPERTY_LIST_URL = CMDB_URL+'cmdb/api/property_list/'
            resp_item_property = requests.get(CMDB_ITEM_PROPERTY_LIST_URL+item_id)
            item_property = json.loads(resp_item_property.text)
            property_list = item_property.get('result').get('res')
            for one_property in property_list:
                p_code = one_property.get('id')
                property_type = one_property.get('type')
                # string 类型
                if 'string' == property_type:
                    value = self.property_mapper.values()[0].get(p_code)
                    if value is None:
                        keys = self.pre_property_mapper.keys()
                        if len(keys) >= 1:
                            value = self.pre_property_mapper.values()[0].get(p_code)
                    if value is not None:
                        transited_property = {
                            'type': property_type,
                            'p_code': p_code,
                            'value': value
                        }
                        transited_property_list.append(transited_property)
                # reference 类型
                elif 'reference' == property_type:
                    reference_ci = one_property.get('reference_ci')
                    reference_id = self.pcode_mapper.get(reference_ci)
                    if reference_id is not None:
                        transited_property = {
                            'type': property_type,
                            'p_code': p_code,
                            'name': one_property.get('name'),
                            'reference_ci': reference_ci,
                            'reference_id': reference_id
                        }
                        transited_property_list.append(transited_property)
            if len(transited_property_list) >= 1:
                repo_item['item_id'] = item_id
                CMDB_URL = current_app.config['CMDB_URL']
                CMDB_ITEM_URL = CMDB_URL+'cmdb/api/cmdb/item/'
                resp_item = requests.get(CMDB_ITEM_URL+item_id)
                item = json.loads(resp_item.text)
                repo_item['name'] = item.get('result').get('res').get('item_name')
                repo_item['property_list'] = transited_property_list
        except Exception as e:
            logging.debug(e.message)
        return repo_item

    def _do_one_item_post(self, item_id):
        repo_item = self.transit_item_property_list(item_id)
        data = json.dumps(repo_item)
        logging.debug("Resource Provider CallBack to CMDB RESTFUL API Post data is:")
        logging.debug(data)
        CMDB_URL = current_app.config['CMDB_URL']
        CMDB_REPO_URL = CMDB_URL+'cmdb/api/repo/'
        resp_repo_item = requests.post(CMDB_REPO_URL, data=data)
        item_property = json.loads(resp_repo_item.text)
        code = item_property.get('code')
        logging.debug("The CMDB RESTFUL API Post Response is:")
        logging.debug(item_property)
        logging.debug("The Response code is :"+code.__str__())
        if 2002 == code:
            p_code = item_property.get('result').get('id')
            self.pcode_mapper[item_id] = p_code
            logging.debug("Add Item(%s): p_code(%s) for self.pcode_mapper" % (item_id, p_code))

    def _do_get_physical_server_for_instance(self, physical_server):
        condition = 'item_id=physical_server&p_code=hostname&value=' + physical_server
        CMDB_URL = current_app.config['CMDB_URL']
        CMDB_REPO_ITEM_CONDITION_GET_URL = CMDB_URL+'cmdb/api/repo_detail/'
        request_url = CMDB_REPO_ITEM_CONDITION_GET_URL + '?' + condition
        resp_repo_item = requests.get(request_url)
        item_property = json.loads(resp_repo_item.text)
        code = item_property.get('code')
        if 2002 == code:
            p_code = item_property.get('result').get('res')[0].get('p_code')
            self.pcode_mapper['physical_server'] = p_code
            logging.debug("Add Item physical_server(%s): p_code(%s) for self.pcode_mapper"
                          % (physical_server, p_code))

    def start(self):
        self.run()

    def run(self):
        while self.state != 'stop':
            self.tick_announce()

    @transition_state_logger
    def do_init(self):
        # 状态机初始状态
        pass

    @transition_state_logger
    def do_stop(self):
        # 停止状态机
        del self

    @transition_state_logger
    def do_deploy_instance(self):
        # 部署实例状态
        self._do_one_item_post('deploy_instance')

    @transition_state_logger
    def do_app_cluster(self):
        # 应用集群状态
        if 'app_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('app_instance', None)
        self._do_one_item_post('app_cluster')

    @transition_state_logger
    def do_app_instance(self):
        # 应用实例状态
        if 'docker' in self.pcode_mapper:
            self.pcode_mapper.pop('docker', None)
        self._do_one_item_post('app_instance')
        physical_server = self.property_mapper.get('app_instance').get('physical_server')
        self._do_get_physical_server_for_instance(physical_server)
        self.docker()

    @transition_state_logger
    def do_docker(self):
        # docker状态
        self._do_one_item_post('docker')

    @transition_state_logger
    def do_mysql_cluster(self):
        # MySQL数据库集群状态
        if 'mysql_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('mysql_instance', None)
        if 'mongodb_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('mongodb_instance', None)
        if 'redis_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('redis_instance', None)
        self._do_one_item_post('mysql_cluster')

    @transition_state_logger
    def do_mysql_instance(self):
        # MySQL数据库实例状态
        if 'virtual_server' in self.pcode_mapper:
            self.pcode_mapper.pop('virtual_server', None)
        self._do_one_item_post('mysql_instance')
        physical_server = self.property_mapper.get('mysql_instance').get('physical_server')
        self._do_get_physical_server_for_instance(physical_server)
        self.virtual_server()

    @transition_state_logger
    def do_mongodb_cluster(self):
        # MongoDB数据库集群状态
        if 'mysql_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('mysql_instance', None)
        if 'mongodb_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('mongodb_instance', None)
        if 'redis_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('redis_instance', None)
        self._do_one_item_post('mongodb_cluster')

    @transition_state_logger
    def do_mongodb_instance(self):
        # MongoDB数据库实例状态
        if 'virtual_server' in self.pcode_mapper:
            self.pcode_mapper.pop('virtual_server', None)
        self._do_one_item_post('mongodb_instance')
        physical_server = self.property_mapper.get('mongodb_instance').get('physical_server')
        self._do_get_physical_server_for_instance(physical_server)
        self.virtual_server()

    @transition_state_logger
    def do_redis_cluster(self):
        # Redis数据库集群状态
        if 'mysql_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('mysql_instance', None)
        if 'mongodb_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('mongodb_instance', None)
        if 'redis_instance' in self.pcode_mapper:
            self.pcode_mapper.pop('redis_instance', None)
        self._do_one_item_post('redis_cluster')

    @transition_state_logger
    def do_redis_instance(self):
        # Redis数据库实例状态
        if 'virtual_server' in self.pcode_mapper:
            self.pcode_mapper.pop('virtual_server', None)
        self._do_one_item_post('redis_instance')
        physical_server = self.property_mapper.get('redis_instance').get('physical_server')
        self._do_get_physical_server_for_instance(physical_server)
        self.virtual_server()

    @transition_state_logger
    def do_virtual_server(self):
        # virtual_server状态
        self._do_one_item_post('virtual_server')


# Transit request_data from the JSON nest structure to the chain structure with items_sequence and porerty_json_mapper
def transit_request_data(items_sequence, porerty_json_mapper, request_data):
    if request_data is None:
        return
    if not (isinstance(items_sequence, list) or isinstance(items_sequence, dict) or isinstance(items_sequence, set)) \
            or not (isinstance(request_data, list) or isinstance(request_data, dict)) \
            or not isinstance(porerty_json_mapper, dict):
        raise Exception("Need input dict for porerty_json_mapper and request_data in transit_request_data.")
    request_items = []
    if isinstance(items_sequence, list) or isinstance(items_sequence, set):
        for one_item_sequence in items_sequence:
            if isinstance(one_item_sequence, dict):
                item_mapper_keys = one_item_sequence.keys()
            elif isinstance(one_item_sequence, basestring):
                item_mapper_keys = [one_item_sequence]
            else:
                raise Exception("Error items_sequence_list_config")
            for item_mapper_key in item_mapper_keys:
                if isinstance(one_item_sequence, basestring):
                    context = None
                else:
                    context = one_item_sequence.get(item_mapper_key)
                item_mapper_body = porerty_json_mapper.get(item_mapper_key)
                if item_mapper_body is not None:
                    if isinstance(request_data, list) or isinstance(request_data, set):
                        for one_req in request_data:
                            item = {}
                            sub_item = copy.deepcopy(one_req)
                            item[item_mapper_key] = sub_item
                            request_items.append(item)
                            if context is not None and sub_item is not None:
                                request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                    else:
                        item = {}
                        current_item = copy.deepcopy(request_data)
                        item[item_mapper_key] = current_item
                        request_items.append(item)
                        if context is not None:
                            if hasattr(current_item, item_mapper_key):
                                sub_item = current_item.get(item_mapper_key)
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                            else:
                                sub_item = current_item
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                else:
                    if request_data is not None:
                        sub_item = request_data.get(item_mapper_key)
                        if context is not None and sub_item is not None:
                            request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
    elif isinstance(items_sequence, dict):
        items_sequence_keys = items_sequence.keys()
        for items_sequence_key in items_sequence_keys:
            context = items_sequence.get(items_sequence_key)
            item_mapper_body = porerty_json_mapper.get(items_sequence_key)
            if item_mapper_body is not None:
                current_items = copy.deepcopy(request_data)
                if hasattr(item_mapper_body, items_sequence_key):
                    current_items_keys = current_items.keys()
                    for current_item_key in current_items_keys:
                        if current_item_key == items_sequence_key:
                            current_item_body = current_items.get(current_item_key)
                            if current_item_body is not None and len(current_item_body) > 0:
                                item = current_items
                                request_items.append(item)
                else:
                    current_item_body = current_items
                    if current_item_body is not None and len(current_item_body) > 0:
                        item = {}
                        item[items_sequence_key] = current_item_body
                        request_items.append(item)
                    if context is not None:
                            if hasattr(current_items, items_sequence_key):
                                sub_item = current_items.get(items_sequence_key)
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                            else:
                                sub_item = current_items
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
            if context is not None and request_data is not None:
                sub_item = request_data.get(items_sequence_key)
                if sub_item is not None:
                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))

    return request_items


# Transit request_items from JSON property to CMDB item property p_code with property_json_mapper
def transit_repo_items(property_json_mapper, request_items):
    if not isinstance(property_json_mapper, dict) and not isinstance(request_items, list):
        raise Exception("Need input dict for property_json_mapper and list for request_items in transit_repo_items.")
    property_mappers_list = []
    for request_item in request_items:
        item_id = request_item.keys()[0]
        repo_property = {}
        item_property_mapper = property_json_mapper.get(item_id)
        item_property_keys = item_property_mapper.keys()
        for item_property_key in item_property_keys:
            value = request_item.get(item_id)
            if value is not None:
                repo_json_property = value.get(item_property_mapper.get(item_property_key))
                if repo_json_property is not None:
                    repo_property[item_property_key] = repo_json_property
        if len(repo_property) >= 1:
            repo_item = {}
            repo_item[item_id] = repo_property
            property_mappers_list.append(repo_item)
    return property_mappers_list


def do_transit_repo_items(items_sequence_list, property_json_mapper, request_data):
    request_items = transit_request_data(items_sequence_list, property_json_mapper, request_data)
    property_mappers_list = transit_repo_items(property_json_mapper, request_items)
    return property_mappers_list


class ResourceProviderCallBack(Resource):
    """
    资源预留回调
    """
    @classmethod
    def post(cls):
        """
Post Request JSON Body：
{
    "username": "袁航",
    "unit_name": "real-final",
    "domain": "",
    "resource_name": "final85",
    "user_id": "143483",
    "resource_id": "7e04ca56-78dc-11e7-879b-fa163e9474c9",
    "cmdb_repo_id": "39d1c166-782f-11e7-b874-fa163e9474c9",
    "unit_id": "39d1c166-782f-11e7-b874-fa163e9474c9",
    "db_info": {
        "redis": {
            "username": "root",
            "password": "123456",
            "mem": 4,
            "cluster_type": "redis",
            "ins_id": "7e051808-78dc-11e7-879b-fa163e9474c9",
            "port": "6379",
            "cluster_name": "361b029ac41b1fbc6310d97a5355522a",
            "instance": [
                {
                    "username": "root",
                    "dbtype": "master",
                    "ip": "172.28.36.177",
                    "instance_name": "361b029ac41b1fbc6310d97a5355522a_0",
                    "instance_type": "redis",
                    "os_inst_id": "d71de71f-da7f-4e9d-bfa5-1885b2092dff",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "6379"
                },
                {
                    "username": "root",
                    "dbtype": "slave",
                    "ip": "172.28.36.178",
                    "instance_name": "361b029ac41b1fbc6310d97a5355522a_1",
                    "instance_type": "redis",
                    "os_inst_id": "014a4024-c4c8-4a6a-b4ce-fa72eca4d668",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "6379"
                }
            ],
            "vip": "172.28.36.180",
            "version": "Redis2.8",
            "cluster_id": "7e051808-78dc-11e7-879b-fa163e9474c9",
            "disk": 50,
            "cpu": 2,
            "quantity": 2
        },
        "mysql": {
            "username": "root",
            "password": "123456",
            "wvip": "172.28.36.18",
            "mem": 4,
            "cluster_type": "mysql",
            "ins_id": "7e050c6e-78dc-11e7-879b-fa163e9474c9",
            "port": "3316",
            "cluster_name": "3105ddb158f0d47381e1e92016294472",
            "instance": [
                {
                    "username": "root",
                    "dbtype": "master",
                    "ip": "172.28.36.17",
                    "instance_name": "3105ddb158f0d47381e1e92016294472_0",
                    "instance_type": "mysql",
                    "os_inst_id": "c6d7ac39-c001-4529-abcb-640d76204e06",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "3316"
                },
                {
                    "username": "root",
                    "dbtype": "slave1",
                    "ip": "172.28.36.176",
                    "instance_name": "3105ddb158f0d47381e1e92016294472_1",
                    "instance_type": "mysql",
                    "os_inst_id": "a1486aba-c459-4fb5-86fc-6c05a20ea700",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "3316"
                },
                {
                    "username": "root",
                    "dbtype": "slave2",
                    "ip": "172.28.36.171",
                    "instance_name": "3105ddb158f0d47381e1e92016294472_2",
                    "instance_type": "mysql",
                    "os_inst_id": "04c36869-5668-41ae-a3a9-cc97f70bfd4d",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "3316"
                },
                {
                    "username": "root",
                    "dbtype": "lvs1",
                    "ip": "172.28.36.167",
                    "instance_name": "3105ddb158f0d47381e1e92016294472_3",
                    "instance_type": "mycat",
                    "os_inst_id": "a9c969b7-e02e-484f-8925-4bf2baa14a97",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "3316"
                },
                {
                    "username": "root",
                    "dbtype": "lvs2",
                    "ip": "172.28.36.175",
                    "instance_name": "3105ddb158f0d47381e1e92016294472_4",
                    "instance_type": "mycat",
                    "os_inst_id": "c36d6624-b7c0-462e-aaa1-48150a1994df",
                    "password": "123456",
                    "physical_server": "osnode011034.syswin.com",
                    "port": "3316"
                }
            ],
            "rvip": "172.28.36.179",
            "version": "MYSQL5.6",
            "cluster_id": "7e050c6e-78dc-11e7-879b-fa163e9474c9",
            "disk": 50,
            "cpu": 2,
            "quantity": 5
        }
    },
    "created_time": "2017-08-04 14:16:46.047000",
    "status": "ok",
    "env": "develop",
    "department": "云服务部",
    "container": [
        {
            "username": "root",
            "domain": "final85-subcluster.syswin.com",
            "mem": 4,
            "cluster_type": "app_cluster",
            "ins_id": "7e0531ee-78dc-11e7-879b-fa163e9474c9",
            "port": "80",
            "cluster_name": "final85-subcluster",
            "instance": [
                {
                    "username": "root",
                    "domain": "final85-subcluster.syswin.com",
                    "ip": "172.28.36.166",
                    "instance_name": "final85-subcluster_0",
                    "instance_type": "app_cluster",
                    "os_inst_id": "28e7b634-0e94-4a83-a72c-10bfc9e168cf",
                    "password": "123456",
                    "physical_server": "osnode011030.syswin.com",
                    "port": "80"
                }
            ],
            "cluster_id": "7e0531ee-78dc-11e7-879b-fa163e9474c9",
            "image_url": "arp.reg.innertoon.com/qitoon.checkin/qitoon.checkin:20170616090015",
            "password": "123456",
            "cpu": 2,
            "quantity": 1
        },
        {
            "username": "root",
            "domain": "final85.syswin.com",
            "mem": 4,
            "cluster_type": "app_cluster",
            "ins_id": "7e052848-78dc-11e7-879b-fa163e9474c9",
            "port": "80",
            "cluster_name": "final85",
            "instance": [
                {
                    "username": "root",
                    "domain": "final85.syswin.com",
                    "ip": "172.28.36.165",
                    "instance_name": "final85_0",
                    "instance_type": "app_cluster",
                    "os_inst_id": "521b7f94-d81e-43af-a1e2-e72dfa8296dc",
                    "password": "123456",
                    "physical_server": "osnode011030.syswin.com",
                    "port": "80"
                }
            ],
            "cluster_id": "7e052848-78dc-11e7-879b-fa163e9474c9",
            "image_url": "arp.reg.innertoon.com/qitoon.checkin/qitoon.checkin:20170616090015",
            "password": "123456",
            "cpu": 2,
            "quantity": 1
        }
    ],
    "unit_des": ""
}
        """
        code = 2002
        request_data = json.loads(request.data)
        resource_id = request_data.get('resource_id')
        status = request_data.get('status')
        try:
            resource = ResourceModel.objects.get(res_id=resource_id)
            resource.reservation_status = status

            is_write_to_cmdb = False
            # TODO: resource.reservation_status全局硬编码("ok", "fail", "reserving", "unreserved")，后续需要统一修改
            if status == "ok":
                is_write_to_cmdb = True

                container = request_data.get('container')
                if container is not None:
                    for i in container:
                        for j in resource.compute_list:
                            if i.get('ins_id') == j.ins_id:
                                j.ips = [ins.get('ip') for ins in i.get('instance')]

                property_mappers_list = do_transit_repo_items(items_sequence_list_config, property_json_mapper_config,
                                                              request_data)
                logging.debug('property_mappers_list 的内容是：%s' % property_mappers_list)

                rpt = ResourceProviderTransitions(property_mappers_list)
                rpt.start()
                if rpt.state == "stop":
                    logging.debug("完成停止")
                else:
                    logging.debug(rpt.state)

            if is_write_to_cmdb is True:
                resource.cmdb_p_code = rpt.pcode_mapper.get('deploy_instance')
         
            os_ids = [] 
            container = request_data.get('container')
            for _container in container:
                instances = _container.get('instance')
                for instance in instances:
                    os_ins_id = instance.get('os_inst_id')
                    os_ids.append(os_ins_id)
                
            db_info = request_data.get('db_info')
            vid_list = []
            for key, value in db_info.items():
                os_ins_ids = []
                wid = value.get("wid", '')
                rid = value.get("rid", '')
                vid = value.get("vid", '')
                if wid:
                    vid_list.append(wid)
                if rid:
                    vid_list.append(rid)
                if vid:
                    vid_list.append(vid)

                for instance in value.get('instance'):
                    os_ins_id = instance.get('os_inst_id')
                    os_ids.append(os_ins_id)
                if os_ins_ids:
                    os_ids.append(os_ins_ids)
            resource.os_ins_list = os_ids
            resource.vid_list = vid_list
            resource.save()
        except Exception as e:
            logging.exception("[UOP] Resource callback failed, Excepton: %s", e.args)
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }
            return ret, code

        res = {
            "code": code,
            "result": {
                "res": "success",
                "msg": "test info"
            }
        }
        return res, 200


res_callback_api.add_resource(ResourceProviderCallBack, '/res')
