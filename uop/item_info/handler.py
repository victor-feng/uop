# -*- coding: utf-8 -*-

import json
import requests
import datetime
import logging

from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from flask import current_app

from uop.item_info import iteminfo_blueprint
from uop.item_info.errors import user_errors
from uop.models import ItemInformation
from config import APP_ENV, configs
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

iteminfo_api = Api(iteminfo_blueprint, errors=user_errors)

null = "null"
#CMDB_URL = current_app.config['CMDB_URL']
CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB_API = CMDB_URL+'cmdb/api/'


class ItemInfo(Resource):
    @classmethod
    def get(cls,item_id):
        res_list = []
        ret = {}
        code = 200
        item_id = "project_item"
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str, location='args')
            parser.add_argument('user_name', type=str, location='args')
            parser.add_argument('item_name', type=str, location='args')
            parser.add_argument('item_code', type=str, location='args')
            parser.add_argument('start_time', type=str, location='args')
            parser.add_argument('end_time', type=str, location='args')
            parser.add_argument('depart', type=str, location='args')
            args = parser.parse_args()

            args_dict = {}
            if args.user_id:
                args_dict["user_id"] = args.user_id
            if args.user_name:
                args_dict["user"] = args.user_name
            if args.item_name:
                args_dict["item_name"] = args.item_name
            if args.item_code:
                args_dict["item_code"] = args.item_code
            if args.depart:
                args_dict["item_depart"] = args.depart
            if args.start_time and args.end_time:
                args_dict['create_date__gte'] = args.start_time
                args_dict['create_date__lt'] = args.end_time
            items = ItemInformation.objects.filter(**args_dict).order_by('-create_date')

            for item in items:
                res = {}
                res["user"] = item.user
                res["user_id"] = item.user_id
                res["item_id"] = item.item_id
                res["item_name"] = item.item_name
                res["item_code"] = item.item_code
                res["item_depart"] = item.item_depart
                res["item_description"] = item.item_description
                res["create_date"] = str(item.create_date)
                res_list.append(res)

            #res = requests.get(CMDB_API + "repo_detail/" + item_id + "/")
            #ret = eval(res.content.decode('unicode_escape'))
        except Exception as e:
            code = 500

        ret = {
            'code': code,
            'result': {
                'res': res_list,
                'msg': ""
            }
        }
        return ret, code

    @classmethod
    def put(cls,item_id):
        ret = {}
        code = 200
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str)
            parser.add_argument('user_name', type=str)
            parser.add_argument('item_name', type=str)
            parser.add_argument('item_code', type=str)
            parser.add_argument('item_department', type=str)
            parser.add_argument('item_description', type=str)
            args = parser.parse_args()

            data = {}
            property_list = []

            if args.item_code:
                property_list.append({"type": "string", "name": "部署单元编号", "value": args.item_code})
            if args.item_name:
                property_list.append({"type": "string", "name": "名称", "value": args.item_name})
            if args.item_department:
                property_list.append({"type": "string", "name": "归属部门", "value": args.item_department})
            if args.item_description:
                property_list.append({"type": "string", "name": "部署单元描述", "value": args.item_description})
            data["property_list"] = property_list
            data_str = json.dumps(data)

            res = requests.put(CMDB_API + "repo/" + item_id + "/", data=data_str)
            ret = eval(res.content.decode('unicode_escape'))
            if res.status_code == 200:
                item = ItemInformation.objects.get(item_id=item_id)
                if args.item_code:
                    item.item_code = args.item_code
                if args.item_name:
                    item.item_name = args.item_name
                if args.item_department:
                    item.item_depart = args.item_department
                if args.item_description:
                    item.item_description = args.item_description
                item.save()

        except Exception as e:
            code = 500

        return ret, code

    @classmethod
    def delete(cls, item_id):
        ret = {}
        code = 200
        try:
            res = requests.delete(CMDB_API + "repo_delete/" + item_id + "/")
            #ret = eval(res.content.decode('unicode_escape'))

            items = ItemInformation.objects.filter(item_id=item_id)
            for item in items:
                item.delete()
        except Exception as e:
            code = 500

        ret = {
            'code': code,
            'result': {
                'res': "",
                'msg': ""
            }
        }
        return ret, code

class ItemPostInfo(Resource):
    def post(self):
        # req = request
        ret = {}
        code = 200
        try:
            parser = reqparse.RequestParser()
            #parser.add_argument('property_list', type=list, required=True, location='json')
            parser.add_argument('user_id', type=str)
            parser.add_argument('user_name', type=str)
            parser.add_argument('item_name', type=str)
            parser.add_argument('item_code', type=str)
            parser.add_argument('item_department', type=str)
            parser.add_argument('item_description', type=str)
            args = parser.parse_args()

            req = CMDB_API + "repo_detail?condition={" "\"item_id\":\"person_item\"," \
                             "\"repoitem_string.default_value\":\""+args.user_id+"\" }"
            res = requests.get(req)
            ret = eval(res.content.decode('unicode_escape'))
            user_p_code = None
            if res.status_code == 200:
                user_p_code = ret.get("result").get("res")[0].get("p_code")

            data = {}
            data["name"] = args.item_name
            data["layer_id"] = "business"
            data["group_id"] = "BusinessLine"
            data["item_id"] = "project_item"

            property_list = []
            property_list.append({"type": "string", "name": "部署单元编号", "value": args.item_code})
            property_list.append({"type": "string", "name": "名称", "value": args.item_name})
            property_list.append({"type": "string", "name": "归属部门", "value": args.item_department})
            property_list.append({"type": "string", "name": "部署单元描述", "value": args.item_description})
            property_list.append({"type": "string", "name": "创建人", "value": args.user_name})
            property_list.append({"type": "string", "name": "创建时间", "value": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            property_list.append({
                            'type': 'reference',
                            'reference_ci': 'person_item',
                            'reference_id': user_p_code,
                            'name': '归属人',
                            })
            data["property_list"] = property_list
            data_str = json.dumps(data)

            res = requests.post(CMDB_API + "repo/", data=data_str)
            ret = eval(res.content.decode('unicode_escape'))
            if res.status_code == 200:
                ItemInformation(
                    user = args.user_name,
                    user_id = args.user_id,
                    item_id = ret.get("result").get("id"),
                    item_name = args.item_name,
                    item_depart= args.item_department,
                    item_description = args.item_description,
                    item_code = args.item_code).save()
        except Exception as e:
            code = 500

        return ret, code

class ItemInfoLoacl(Resource):
    def get(self,user_id):
        code = 200
        res_list = []
        try:
            items = ItemInformation.objects.filter(user_id = user_id)
            for i in items:
                res = {}
                res["user"] = i.user
                res["user_id"] = i.user_id
                res["item_id"] = i.item_id
                res["item_name"] = i.item_name
                res["item_code"] = i.item_code
                res["item_depart"] = i.item_depart
                res["item_description"] = i.item_description
                res_list.append(res)
        except Exception as e:
            code = 500

        ret = {
            'code': code,
            'result': {
                'res': res_list,
                'msg': ""
            }
        }
        return ret, code

iteminfo_api.add_resource(ItemInfo, '/iteminfoes/<string:item_id>')
iteminfo_api.add_resource(ItemInfoLoacl, '/iteminfoes/local/<string:user_id>')
iteminfo_api.add_resource(ItemPostInfo, '/iteminfoes')
