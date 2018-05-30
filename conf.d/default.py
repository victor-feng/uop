# -*- coding: utf-8 -*-
import os
import json
basedir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
print basedir


def get_entity_from_local_file():
    # entity_dir = basedir + "/uop/entity.txt"
    with open(basedir + "/uop/entity.txt", "rb") as f:
        entity = json.load(f)
        CMDB2_ENTITY = {
            "Person": entity.get("Person", ""),
            "department": entity.get("department", ""),
            "yewu": entity.get("yewu", ""),
            "Module": entity.get("Module", ""),
            "project": entity.get("project", ""),
            "host": entity.get("host", ""),
            "container": entity.get("container", ""),
            "virtual_device": entity.get("virtual_device", ""),
            "tomcat": entity.get("tomcat", ""),
            "mysql": entity.get("mysql", ""),
            "redis": entity.get("redis", ""),
            "mongodb": entity.get("mongodb", ""),
            "nginx": entity.get("nginx", ""),
            "rabbitmq": entity.get("rabbitmq", ""),
            "codis": entity.get("codis", ""),
            "apache": entity.get("apache", ""),
            "zookeeper": entity.get("zookeeper", ""),
            "mycat": entity.get("mycat", "")
        }
        CMDB2_VIEWS = {
            # 注意：定时任务只会缓存1，2，3 三个视图下的基础模型数据
            "1": ("B7", u"工程 --> 物理机，用于拿到各层间实体关系信息", entity.get("project", "")),  # （视图名，描述，起点实体id）
            "2": ("B6", u"部门 --> 资源，用于分级展示业务模块工程", entity.get("department", "")),
            "3": ("B5", u"人 --> 部门 --> 工程", entity.get("Person", "")),

            "4": ("B8", u"tomcat --> 机房，展示tomcat资源视图", entity.get("tomcat", "")),
            "5": ("B9", u"mysql --> 机房，展示mysql资源视图", entity.get("mysql", "")),
            "6": ("B10", u"mongodb--> 机房，展示mongodb资源视图", entity.get("mongodb", "")),
            "7": ("B11", u"redis --> 机房，展示redis资源视图", entity.get("redis", "")),
            "8": ("B12", u"物理机信息", entity.get("host", "")),
            "9": ("B13", u"模块 --> 物理机，用于拿到各层间实体关系信息", entity.get("Module", "")),
            "10": ("B14", u"nginx --> 机房，展示nginx资源视图", entity.get("nginx", "")),
            "11": ("B15", u"rabbitmq --> 机房，展示rabbitmq资源视图", entity.get("rabbitmq", "")),
            "12": ("B16", u"codis --> 机房，展示codis资源视图", entity.get("codis", "")),
            "13": ("B17", u"apache --> 机房，展示apache资源视图", entity.get("apache", "")),
            "14": ("B18", u"zookeeper --> 机房，展示zookeeper资源视图", entity.get("zookeeper", "")),
            "15": ("B19", u"mycat --> 机房，展示mycat资源视图", entity.get("mycat", "")),
        }
        return CMDB2_ENTITY, CMDB2_VIEWS