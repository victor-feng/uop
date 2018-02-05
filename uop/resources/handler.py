# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
import copy
import time
import random
import datetime
from uop.log import Log
from uop.util import async
from config import APP_ENV, configs
from uop.models import ResourceModel
from uop.item_info.handler import delete_instance
from flask import jsonify
import  xlsxwriter
import uuid
import sys,os

reload(sys)
sys.setdefaultencoding('utf-8')

CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB2_URL = configs[APP_ENV].CMDB2_URL
CRP_URL = configs[APP_ENV].CRP_URL
UPLOAD_FOLDER=configs[APP_ENV].UPLOAD_FOLDER


__all__ = [
    "make_random_database_password", "_match_condition_generator",
]

status_dict={
    "active":u"运行中",
    "error":u"错误",
    "shutoff":u"关机",
    "failed":u"虚机不存在",
    "rebuild":u"部署中",
    '':u''
}

field_dict={
    "resource_type":u"实例类型",
	"resource_name":u"资源名称",
	"env":u"所属环境",
	"project_name":u"所属工程",
    "module_name":u"所属模块",
    "business_name":u"所属业务",
    "domain":u"域名",
	"create_date":u"创建日期",
    "update_time":u"修改日期",
	"resource_ip":u"IP",
	"resource_config":u"配置",
	"resource_status":u"状态",
}

class ExcelException(object):
    pass


def make_random_database_password():
    return str(random.randint(100000, 999999)) + chr(random.randint(65, 90)) + chr(
        random.randint(97, 122)) + '!'


def _match_condition_generator(args):
    match = dict()
    if args.user_id or args.resource_name or args.project or args.formStatus or args.approval_status\
            or (args.start_time and args.end_time):
        match_cond = dict()
        match_dict = dict()
        match_list = []
        if args.user_id:
            match_cond['user_id'] = args.user_id
        if args.resource_name:
            match_cond['resource_name'] = args.resource_name
        if args.project:
            match_cond['project'] = args.project
        if args.formStatus:
            match_cond['application_status'] = args.formStatus
        if args.approval_status:
            match_cond['approval_status'] = args.approval_status
        if args.department:
            match_cond["department"]=args.department
        if args.start_time and args.end_time:
            created_date_dict = dict()
            created_date_dict['$gte'] = datetime.datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
            created_date_dict['$lte'] = datetime.datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")
            match_cond['created_date'] = created_date_dict
        match_list.append(match_cond)
        match_dict['$and'] = match_list
        match['$match'] = match_dict
    return match


def pageinit(items, offset, limit):
    if offset < 0 or limit < 0:
        return []
    assert isinstance(items, list)
    total_len = len(items)
    pages = total_len / limit
    o_page = 1 if total_len % limit else 0
    total_pages = pages + o_page
    total_pages = total_pages if total_pages else 1
    if total_pages > offset:
        pre = (offset - 1) * limit
        last = offset * limit
        page_contents = items[pre:last]
    elif total_pages == offset:
        pre = (offset - 1) * limit
        page_contents = items[pre:]
    else:
        page_contents = []
    return page_contents, total_pages


def get_from_cmdb2(args, filters, download=False):
    url = CMDB2_URL + "cmdb/openapi/resourcs/list/"
    response = {
        "code": 2002,
        "result": {
            "msg": "success",
            "res": {
                "current_page": filters["page_num"],
                "object_list": [],
                "total_page": 0
            }
        }
    }
    try:
        Log.logger.info("args:{}".format( args))
        ret = requests.post(url, data=json.dumps(args), timeout=60).json()
        if ret["code"] != 0:
            response["code"] = ret["code"]
            response["result"]["msg"] = ret["msg"]
        # Log.logger.info(u"部门：{}".format(filters["dep"]))
        resources = ResourceModel.objects.filter(department=filters["dep"], env=filters["env"])
        cmdb2_resource_id_list = []
        for res in resources:
            for id in res.cmdb2_resource_id:
                cmdb2_resource_id_list.append(str(id))
        data = [r for r in ret["data"] if str(r.get("id")) in cmdb2_resource_id_list] if filters["dep"] != "admin" else ret["data"]
        # Log.logger.info("cmdb2_resource_id_list:{}， data:{}, ret:{}".format(cmdb2_resource_id_list, data, ret))
        if download:
            return parse_data_uop(data, filters)
        object_list, total_page = pageinit(data, int(filters["page_num"]), int(filters["page_count"]))
        response["result"]["res"]["object_list"] = [{k.lower(): v for k, v in ol.items()} for ol in object_list]
        response["result"]["res"]["total_page"] = total_page
    except Exception as exc:
        response["code"] = 500
        response["result"]["msg"] = str(exc)
    return jsonify(response)


def parse_data_uop(data, filters):

    return data


def to_unicode(value):
    try:
        """将字符转为 unicode 编码
        @param {string} value 将要被转码的值
        @return {unicode} 返回转成 unicode 的字符串
        """
        if value == None:
            return None
        if isinstance(value, unicode):
            return value
        # 字符串类型,需要按它原本的编码来解码出 unicode,编码不对会报异常
        if isinstance(value, str):
            for encoding in ("utf-8", "gbk", "cp936", sys.getdefaultencoding(), "gb2312", "gb18030", "big5", "latin-1", "ascii"):
                try:
                    value = value.decode(encoding)
                    break # 如果上面这句执行没错，说明是这种编码
                except:
                    pass
        # 其它类型
        return value
    except Exception,e:
        err_msg='execute to_unicode error: %s' % str(e)
        raise ExcelException(err_msg)


def deal_myresource_to_excel(data,field_list):
    try:
        excel_name="myresource_" + str(uuid.uuid1()) +'.xlsx'
        download_dir = os.path.join(UPLOAD_FOLDER, 'excel')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        excel = "%s/%s" % (download_dir,excel_name)
        workbook = xlsxwriter.Workbook(excel)
        worksheetResource = workbook.add_worksheet(u'我的资源')
        worksheetResource.set_column(0, 31, 18)
        head = workbook.add_format(
            {'border': 1, 'align': 'center', 'bg_color': '6699ff', 'font_size': 10, 'font_name': u'微软雅黑', 'bold': True,
             'text_wrap': True, 'valign': 'vcenter'})
        body = workbook.add_format({'border': 1, 'align': 'center', 'font_size': 10, 'font_name': u'微软雅黑'})
        head_cols=[]
        if len(field_list) == 0:
            field_list=["resource_type","resource_name","business_name","env","project_name","create_date","resource_ip","resource_config","resource_status","update_time","domain","module_name"]
        for field in field_list:
            head_cols.append(field_dict[field])
        res_list=deal_data(data, field_list)
        for i in range(0,len(head_cols)):
            h_col = to_unicode(head_cols[i])
            worksheetResource.write(0,i,h_col,head)
        for j in range(0,len(res_list)):
            for i in range(0,len(head_cols)):
                res=to_unicode(res_list[j][i])
                worksheetResource.write(1 + j, i, res, body)
        workbook.close()
        return "success",excel_name
    except Exception as e:
        err_msg= "deal my resource to excel error: %s" % str(e)
        return  err_msg,excel_name


def deal_data(data,field_list):
    res_list=[]
    try:
        for d in data:
            res=[]
            for field in field_list:
                if field == 'resource_config':
                    resource_config=d.get('resource_config',[
                                    {
                                        "name": "CPU",
                                        "value": "2\u6838"
                                    },
                                    {
                                        "name": "\u5185\u5b58",
                                        "value": "2GB"
                                    }
                                ])
                    cpu_name=resource_config[0].get('name')
                    cpu_value = resource_config[0].get('value').split('\\')[0] + u'核'
                    mem_name = "内存"
                    mem_value = resource_config[1].get('value')
                    config="%s:%s %s:%s"% (cpu_name,cpu_value,mem_name,mem_value)
                    res.append(config)
                elif field == "resource_status":
                    status = status_dict[d.get('resource_status', '')]
                    res.append(status)
                else:
                    field_data = d.get(field,'')
                    res.append(field_data)
            res_list.append(res)
        return res_list
    except Exception as e:
        err_msg= "deal my resource data error: %s" % str(e)
        raise ExcelException(err_msg)


def delete_cmdb1(code):
    cmdb_url = '%s%s%s' % (CMDB_URL, 'cmdb/api/repores_delete/', code)
    requests.delete(cmdb_url)


@async
def delete_cmdb2(res_id):
    resource = ResourceModel.objects.filter(res_id=res_id)
    instance_list = []
    if resource:
        null = [instance_list.extend(res.cmdb2_resource_id) for res in resource if res.cmdb2_resource_id]
    class args(object):
        delete_list = instance_list
    ret = delete_instance(args)
    Log.logger.info("testdeltecmdb:{}".format(ret))