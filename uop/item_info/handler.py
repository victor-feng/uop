# -*- coding: utf-8 -*-
import json
import requests
import datetime
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.item_info import iteminfo_blueprint
from uop.item_info.errors import user_errors

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

iteminfo_api = Api(iteminfo_blueprint, errors=user_errors)

null = "null"
#url = "http://172.28.11.111:8001/cmdb/api/"
url = "http://cmdb-test.syswin.com/cmdb/api/"
#url = "http://172.28.20.124/cmdb/api/"
class ItemInfo(Resource):
    @classmethod
    def get(cls,item_id):
        ret = {}
        code = 200
        item_id = "project_item"
        try:
            parser = reqparse.RequestParser()
            args = parser.parse_args()
            res = requests.get(url + "repo_detail/" + item_id + "/")
            ret = eval(res.content.decode('unicode_escape'))
        except Exception as e:
            code = 500

        return ret, code

    @classmethod
    def put(cls,item_id):
        ret = {}
        code = 200
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('property_list', type=list, required=True, location='json')
            args = parser.parse_args()

            data = {}
            data["property_list"] = args.property_list
            data_str = json.dumps(data)

            res = requests.put(url + "repo/" + item_id + "/",data = data_str)
            ret = eval(res.content.decode('unicode_escape'))
        except Exception as e:
            code = 500

        return ret, code

    @classmethod
    def delete(cls, item_id):
        ret = {}
        code = 200
        try:
            res = requests.delete(url + "repo_delete/" + item_id + "/")
            ret = eval(res.content.decode('unicode_escape'))
        except Exception as e:
            code = 500

        return ret, code

class ItemPostInfo(Resource):
    @classmethod
    def post(cls):
        # req = request
        ret = {}
        code = 200
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('property_list', type=list, required=True, location='json')
            parser.add_argument('name', type=str)
            #parser.add_argument('layer_id', type=str)
            #parser.add_argument('group_id', type=str)
            #parser.add_argument('item_id', type=str)
            args = parser.parse_args()

            data = {}
            data["name"] = args.name
            data["layer_id"] = "business"
            data["group_id"] = "BusinessLine"
            data["item_id"] = "project_item"

            args.property_list.append({"type" : "datetime","name" : "创建日期","value" : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            data["property_list"] = args.property_list
            data_str = json.dumps(data)

            res = requests.post(url + "repo/", data=data_str)
            ret = eval(res.content.decode('unicode_escape'))
        except Exception as e:
            code = 500

        return ret, code

iteminfo_api.add_resource(ItemInfo, '/iteminfoes/<string:item_id>')
iteminfo_api.add_resource(ItemPostInfo, '/iteminfoes')
