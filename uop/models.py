# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask_mongoengine import MongoEngine
db = MongoEngine()



class ViewCache(db.Document):
    view_id = db.StringField(required=True)
    relation = db.StringField(default="")
    entity = db.StringField(default="")

    cache_date = db.DateTimeField()
    meta = {
        'indexes': [
            'view_id',
            {
                'fields': ['cache_date'],
                'expireAfterSeconds': 60 * 60 * 24
            }
        ]
    }


class ModelCache(db.Document):
    entity = db.StringField(default="")
    cache_date = db.DateTimeField()
    meta = {
        'indexes': [
            'entity',
            {
                'fields': ['cache_date'],
                'expireAfterSeconds': 60 * 60 * 24
            }
        ]
    }

class HostsCache(db.Document):
    instance_id = db.StringField(default="", unique=True)
    ip = db.StringField(required=False)
    name = db.StringField(required=False)
    cache_date = db.DateTimeField()
    meta = {
        'indexes': [
            'instance_id',
            {
                'fields': ['cache_date'],
                'expireAfterSeconds': 60 * 60 * 24 * 7
            }
        ]
    }

class Token(db.Document):
    token = db.StringField()
    uid = db.IntField()
    token_date = db.DateTimeField()
    meta = {
        'indexes': [
            'uid',
            {
                'fields': ['token_date'],
                'expireAfterSeconds': 60 * 20
            }
        ]
    }


class Cmdb(db.Document):
    username = db.StringField()
    password = db.StringField()


class Statusvm(db.DynamicDocument):
    """
    虚拟机状态表
    """
    resource_name = db.StringField(required=True)
    resource_id = db.StringField(required=True)
    resource_view_id = db.StringField(required=False)
    view_num = db.StringField(required=False)
    business_name = db.StringField(required=True)
    module_name = db.StringField(required=True)
    project_name = db.StringField(required=True)
    project_id = db.StringField(required=True)

    cpu = db.StringField(required=False)
    env = db.StringField(required=True)
    mem = db.StringField(required=False)
    osid = db.StringField(required=True)
    ip = db.StringField(required=False)
    os_type = db.StringField(required=False)

    user_id = db.StringField(required=False)
    status = db.StringField(required=True)
    create_time = db.DateTimeField(required=False)
    update_time = db.DateTimeField(required=False)
    domain = db.StringField(required=False)
    domain_ip = db.StringField(required=False)
    department = db.StringField(required=False)

    meta = {
            'collection': 'status_vm',
            'indexes': [
                {
                    'fields': ['osid',"resource_name"],
                    'unique': False,
                }
            ],
            }

    @classmethod
    def created_status(cls, **kwargs):
        params = {}
        for k, v in kwargs.items():
            if k in ["create_time","update_time"]:
                if v:
                    v = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                else:
                    v = datetime.now()
                params.update({"update_time": v})
            params.update({k: v})
        try:
            c = Statusvm(**params)
            c.save()
        except Exception as e:
            code = 500
            logging.error("created_status error:{}".format(str(e)))
            return False
        return True


class PermissionList(db.Document):
    perm_id= db.StringField(required=True, max_length=50,unique=True)
    name = db.StringField(required=True, max_length=50, unique=True,unique_with='role')
    menu_id = db.StringField(required=False, max_length=50)
    role = db.StringField(required=False, max_length=50)
    button = db.StringField(required=False)
    icon=db.StringField(required=False)
    operation=db.StringField(required=False)
    url = db.StringField(required=False)
    perm_type=db.StringField(required=False)
    endpoint=db.StringField(required=False)
    api_get = db.StringField(required=False,default='0')
    api_post = db.StringField(required=False,default='0')
    api_put = db.StringField(required=False,default='0')
    api_delete = db.StringField(required=False,default='0')
    parent_id = db.StringField(required=False, max_length=50)
    level = db.StringField(required=False, max_length=50)
    created_time = db.DateTimeField(auto_now_add=True, default=datetime.now())
    updated_time = db.DateTimeField(auto_now_add=True, default=datetime.now())
    isDropdown = db.BooleanField(required=False)
    menu_index=db.IntField(required=False, max_length=50)

    meta = {
            "collection": "permission_list",
            "index": [{
                'fields': ['name', 'id'],
                'unique': True,
                }]
            }


class UserInfo(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    username = db.StringField(required=False, max_length=50)
    password = db.StringField(required=True, max_length=50)
    department = db.StringField(required=False)
    role = db.StringField(required=False,max_length=50)
    is_admin = db.BooleanField(required=False, default=False)
    is_external = db.BooleanField(required=False, default=False)
    created_time = db.DateTimeField(auto_now_add=True, default=datetime.now())
    updated_time = db.DateTimeField(auto_now_add=True, default=datetime.now())
    last_login_time = db.DateTimeField(auto_now_add=True, default=datetime.now())

    meta = {
            "collection": "uop_userinfo",
            "index": [{
                'fields': ['username', 'id', 'department', 'is_admin'],
                'unique': True,
                }]
            }


class RoleInfo(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    name = db.StringField(required=True, max_length=50,unique=True)
    description = db.StringField(required=False)
    updated_time = db.DateTimeField(auto_now_add=True, default=datetime.now())
    created_time = db.DateTimeField(auto_now_add=True, default=datetime.now())

    meta = {
            "collection": "roleinfo",
            "index": [{
                'fields': ['role', 'id'],
                'unique': True,
                }]
            }


class DisconfIns(db.EmbeddedDocument):
    ins_name = db.StringField(required=True)
    ins_id = db.StringField(required=True)
    disconf_tag = db.StringField(required=False)
    disconf_name = db.StringField(required=False)
    disconf_content = db.StringField(required=False)
    disconf_admin_content = db.StringField(required=False)
    disconf_server_name = db.StringField(required=False)
    disconf_server_url = db.StringField(required=False)
    disconf_server_user = db.StringField(required=False)
    disconf_server_password = db.StringField(required=False)
    disconf_version = db.StringField(required=False)
    disconf_env = db.StringField(required=False)
    disconf_id = db.StringField(required=False)
    disconf_app_name = db.StringField(required=False)
    meta = {
        'collection': 'disconf_ins',
        'index': [
            {
                'fields': ['ins_name','ins_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }


class Deployment(db.Document):
    deploy_id = db.StringField(required=True, unique=True)
    initiator = db.StringField()
    project_id = db.StringField()
    project_name = db.StringField()
    resource_id = db.StringField()
    deploy_name = db.StringField(required=True, unique_with='resource_id')
    resource_name = db.StringField()
    created_time = db.DateTimeField(default=datetime.now())
    environment = db.StringField()
    release_notes = db.StringField()
    mysql_tag = db.StringField()
    mysql_context = db.StringField()
    redis_tag = db.StringField()
    redis_context = db.StringField()
    mongodb_tag = db.StringField()
    mongodb_context = db.StringField()
    app_image = db.StringField()
    deploy_result = db.StringField()
    user_id = db.StringField()
    database_password = db.StringField()  # 数据库用户的密码
    apply_status = db.StringField()  # 部署申请状态
    approve_status = db.StringField()  # 部署审批状态
    approve_suggestion = db.StringField()  # 审批意见
    deploy_type = db.StringField()  # 部署类型
    disconf_list = db.ListField(db.EmbeddedDocumentField('DisconfIns'))
    is_deleted = db.IntField(required=False, default=0)
    is_rollback = db.IntField(required=False, default=0)
    deleted_time = db.DateTimeField(default=datetime.now())
    capacity_info = db.StringField(required=False, default="{}")
    department = db.StringField()

    module_name = db.StringField(required=False)
    business_name = db.StringField(required=False)
    resource_type = db.StringField(required=False)  # 资源的类型是应用app，数据库 database

    meta = {
        'collection': 'deployment',
        'index': [
            {
                'fields': ['deploy_id', 'deploy_name'],
                'sparse': True,
                }
            ],
        'index_background': True
    }


class ComputeIns(db.EmbeddedDocument):
    ins_name = db.StringField(required=False)
    ins_id = db.StringField(required=False)
    # ins_type = db.StringField(required=False)
    cpu = db.IntField(required=False)
    mem = db.IntField(required=False)
    # disk = db.StringField(required=False)
    domain = db.StringField(required=False)
    domain_ip = db.StringField(required=False)
    domain_path = db.StringField(required=False)
    quantity = db.IntField(required=False)
    # version = db.StringField(required=False)
    ips = db.ListField(required=False)
    url = db.StringField(required=False)
    port = db.StringField(required=False)
    docker_meta = db.StringField(required=False)
    capacity_list = db.ListField(db.EmbeddedDocumentField('Capacity'), default=[])
    health_check = db.IntField(required=False)
    network_id = db.StringField(required=False)
    networkName = db.StringField(required=False)
    certificate = db.StringField(required=False)
    tenantName = db.StringField(required=False)
    host_env = db.StringField(required=False)  # 宿主机环境 docker，kvm，physical_server
    language_env = db.StringField(required=False)  # 语言环境，python，java，php
    deploy_source = db.StringField(required=False)  # 部署来源，image，war，git
    database_config = db.StringField(required=False) # java tomcat 数据库配置
    lb_methods = db.StringField(required=False)  #负载均衡算法,round_robin 轮询,least_conn 最少连接,ip_hash 会话保持
    namespace = db.StringField(required=False) #k8s 命名空间
    ready_probe_path = db.StringField(required=False) #就绪探针路径
    host_mapping = db.StringField(required=False)  # 就绪探针路径


    meta = {
        'collection': 'compute_ins',
        'index': [
            {
                'fields': ['ins_name', 'ins_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }

class Capacity(db.EmbeddedDocument):
    capacity_id = db.StringField(required=True)
    # 变更数 - 当前数
    #numbers = db.IntField(required=False)
    begin_number=db.IntField(required=False)
    end_number = db.IntField(required=False)
    created_date = db.DateTimeField(default=datetime.now())
    network_id = db.StringField(required=False, default="")
    meta = {
        'collection': 'capacity',
        'index': [
            {
                'fields': ['capacity_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }


class DBIns(db.EmbeddedDocument):
    ins_name = db.StringField(required=False)
    ins_id = db.StringField(required=False)
    ins_type = db.StringField(required=False)
    cpu = db.IntField(required=False)
    mem = db.IntField(required=False)
    disk = db.IntField(required=False)
    quantity = db.IntField(required=False, default_value=0)
    version = db.StringField(required=False)
    volume_size = db.IntField(required=False, default_value=0)
    network_id = db.StringField(required=False)
    image_id = db.StringField(required=False)
    meta = {
        'collection': 'db_ins',
        'index': [
            {
                'fields': ['ins_name', 'ins_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }

class OS_ip_dic(db.EmbeddedDocument):
    ip=db.StringField(required=False)
    os_ins_id = db.StringField(requirquired=False)
    os_vol_id = db.StringField(requirquired=False)
    os_type = db.StringField(required=False)
    cpu = db.StringField(required=False)
    mem = db.StringField(required=False)
    instance_id = db.StringField(required=False)
    wvip = db.StringField(required=False)
    rvip = db.StringField(required=False)
    vip = db.StringField(required=False)
    port = db.StringField(required=False)

    meta = {
        'collection': 'os_ip_dic',
        'index': [
            {
                'fields': ['ip'],
                'sparse': True,
                }
            ],
        'index_background': True
        }


class ResourceModel(db.DynamicDocument):
    resource_name = db.StringField(required=True)
    project = db.StringField(required=True)
    project_id = db.StringField(required=False)
    cmdb2_project_id = db.StringField(required=False)
    cmdb2_resource_id = db.ListField(db.StringField(requeired=False))

    project_name = db.StringField(required=False)
    module_name = db.StringField(required=False)
    business_name = db.StringField(required=False)

    department = db.StringField(required=True)
    department_id = db.StringField(required=True)
    deploy_name = db.StringField()
    res_id = db.StringField(required=True, unique=True)
    user_name = db.StringField(required=False)
    user_id = db.StringField(required=False)
    # created_date = db.DateTimeField(default=datetime.now())
    created_date = db.DateTimeField(required=False)
    domain = db.StringField(required=False)
    env = db.StringField(required=True, unique_with= 'resource_name')
    application_status = db.StringField(required=False)
    approval_status = db.StringField(required=False)
    reservation_status = db.StringField(required=False)
    resource_list = db.ListField(db.EmbeddedDocumentField('DBIns'))
    compute_list = db.ListField(db.EmbeddedDocumentField('ComputeIns'))
    cmdb_p_code = db.StringField(requeired=False)
    os_ins_list = db.ListField(db.StringField(requeired=False))
    os_ins_ip_list = db.ListField(db.EmbeddedDocumentField('OS_ip_dic'))
    vid_list = db.ListField(db.StringField(requeired=False))
    is_rollback = db.IntField(required=False, default=0)
    is_deleted = db.IntField(required=False, default=0)
    deleted_date = db.DateTimeField(required=False)
    docker_network_id = db.StringField(required=False)
    mysql_network_id = db.StringField(required=False)
    redis_network_id = db.StringField(required=False)
    mongodb_network_id = db.StringField(required=False)
    cloud = db.StringField(required=False) #1 = cloud1.0 ,2=cloud2.0
    resource_type = db.StringField(required=False) #资源的类型是应用app，数据库 database



    meta = {
        'collection': 'resources',
        'indexes': [
            {
                'fields': ['res_id', ('resource_name', 'env')],
                'sparse': True,
                }
            ],
        'index_background': True
        }


class Approval(db.DynamicDocument):
    approval_id = db.StringField(required=True, max_length=50, unique=True)
    resource_id = db.StringField(required=True)
    deploy_id = db.StringField(required=False)
    project_id = db.StringField(required=True)
    department = db.StringField(required=True)
    user_id = db.StringField(required=True)
    create_date = db.DateTimeField(default=datetime.now())
    approve_uid = db.StringField(required=False)
    approve_date = db.DateTimeField(required=False)
    # processing/success/failed
    approval_status = db.StringField(required=True)
    annotations = db.StringField(required=False,max_length=500)
    capacity_status = db.StringField(required=False, default='res')

    meta = {
        'collection': 'approval',
        'index': [
            {
                'fields': ['resource_id', 'approval_status'],
                'sparse': True,
                }
            ],
        'index_background': True
    }

class ItemInformation(db.DynamicDocument):
    user = db.StringField(required=True)
    user_id = db.StringField(required=True)
    item_id = db.StringField(required=True)
    item_name = db.StringField(required=True, unique=True)
    item_code = db.StringField(required=True)
    item_depart = db.StringField(required=True)
    item_description = db.StringField(required=False)
    create_date = db.DateTimeField(default=datetime.now)
    deleted = db.IntField(required=False, default=0)


    meta = {
        'collection': 'item_information',
        'index': [
            {
                'fields': ['item_id'],
                'sparse': True,
                }
            ],
        'index_background': True
    }

#class ConfigureEnv(db.DynamicDocument):
class ConfigureEnvModel(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    name = db.StringField(required=False, max_length=50)

    meta = {
            "collection": "configure_env",
            "index": [{
                'fields': ['id'],
                'unique': True,
                }]
            }

class ConfigureDisconfModel(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    env = db.StringField(required=False, max_length=50)
    name = db.StringField(required=False, max_length=50)
    username = db.StringField(required=False, max_length=50)
    password = db.StringField(required=False, max_length=50)
    ip = db.StringField(required=False, max_length=50)
    url = db.StringField(required=False, max_length=50)

    meta = {
            "collection": "configure_disconf",
            "index": [{
                'fields': ['id'],
                'unique': True,
                }]
            }


class ConfigureNginxModel(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    env = db.StringField(required=False, max_length=50)
    name = db.StringField(required=False, max_length=50)
    ip = db.StringField(required=False, max_length=50)

    meta = {
            "collection": "configure_nginx",
            "index": [{
                'fields': ['id'],
                'unique': True,
                }]
            }

class StatusRecord(db.Document):
    deploy_id = db.StringField()
    res_id = db.StringField()
    #resource_name = db.StringField()
    #deploy_name = db.StringField()
    created_time = db.DateTimeField(default=datetime.now())
    status = db.StringField(default='')  # 状态
    msg = db.StringField(default='')  # 状态信息
    s_type = db.StringField(default='')
    docker = db.ListField(db.StringField())
    mongo = db.ListField(db.StringField())
    redis = db.ListField(db.StringField())
    mysql = db.ListField(db.StringField())
    is_deleted = db.IntField(required=False, default=0)
    set_flag = db.StringField(default='')
    unique_flag = db.StringField()

    meta = {
        'collection': 'status_record',
        'index': [
            {
                'fields': ['status', 'resource_name', 'deploy_name'],
                'sparse': True,
            }
        ],
        'index_background': True
    }

class OperationLog(db.Document):
    deploy_id = db.StringField()
    res_id = db.StringField()
    created_time = db.DateTimeField(default=datetime.now())
    msg = db.StringField()  

    meta = {
        'collection': 'operation_log',
        'index': [
            {
                'fields': ['res_id', 'deploy_id'],
                'sparse': True,
            }
        ],
        'index_background': True
    }

class NetWorkConfig(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    name = db.StringField()
    env = db.StringField()
    created_time = db.DateTimeField(default=datetime.now())
    sub_network = db.StringField(default='')
    vlan_id = db.StringField(default='',)
    networkName = db.StringField(default='',)
    tenantName = db.StringField(default='',)
    is_deleted = db.IntField(required=False, default=0)
    cloud = db.StringField(required=False)

    meta = {
        'collection': 'network_config',
        'index': [
            {
                'fields': ['env', 'name'],
                'sparse': True,
            }
        ],
        'index_background': True
    }


class ConfigureK8sModel(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    env = db.StringField(required=False, max_length=50)
    namespace_name = db.StringField(required=False)
    config_map_name = db.StringField(required=False)



    meta = {
            "collection": "configure_k8s",
            "index": [{
                'fields': ['id'],
                'unique': True,
                }]
            }

class ConfOpenstackModel(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    env = db.StringField(required=False, max_length=50)
    image_id = db.StringField(required=False)
    image_name = db.StringField(required=False)
    cloud = db.StringField(required=False)

    config_map_name = db.StringField(required=False)



    meta = {
            "collection": "configure_k8s",
            "index": [{
                'fields': ['id'],
                'unique': True,
                }]
            }
