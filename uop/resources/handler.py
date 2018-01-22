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
from config import APP_ENV, configs
import  xlsxwriter
import uuid
import sys

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
    "active":"运行中",
    "error":"错误",
    "shutoff":"关机",
    "failed":"虚机不存在",
    "rebuild": "部署中",
    '':''
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



def deal_myresource_to_excel(data):
    try:
        excel_name="myresource" + str(uuid.uuid1())
        excel = "%s/%s.xlsx" % (configs[APP_ENV],excel_name)
        workbook = xlsxwriter.Workbook(excel)
        worksheetResource = workbook.add_worksheet(u'我的资源')
        worksheetResource.set_column(0, 31, 18)
        head = workbook.add_format(
            {'border': 1, 'align': 'center', 'bg_color': '6699ff', 'font_size': 10, 'font_name': u'微软雅黑', 'bold': True,
             'text_wrap': True, 'valign': 'vcenter'})
        body = workbook.add_format({'border': 1, 'align': 'center', 'font_size': 10, 'font_name': u'微软雅黑'})
        head_cols=[u"实例类型",u"部署实例名称",u"所属环境",u"所属部署单元",u"创建日期",u"IP",u"配置",u"状态"]
        res_list=deal_data(data)
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

def deal_data(data):
    res_list=[]
    try:
        for d in data:
            res=[]
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
            res.append(d.get('resource_type',''))
            res.append(d.get('resource_name',''))
            res.append(d.get('env',''))
            res.append(d.get('item_name',''))
            res.append(d.get('create_date', ''))
            res.append(d.get('resource_ip', ''))
            res.append(config)
            status=status_dict[d.get('resource_status', '')]
            res.append(status)
            res_list.append(res)
        return res_list
    except Exception as e:
        err_msg= "deal my resource data error: %s" % str(e)
        raise ExcelException(err_msg)
