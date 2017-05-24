# -*- coding: utf-8 -*-
import json
import requests
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.workbench import bench_blueprint
from uop.models import User, ItemInformation
from uop.workbench.errors import user_errors

bench_api = Api(bench_blueprint, errors=user_errors)
url = 'http://cmdb-test.syswin.com/cmdb/api/repo_detail/project_item'


class SourceUnitList(Resource):
    def get(self):
        r = requests.get(url)
        res = []
        res_list = []
        for i in json.loads(r.text).get('result').get('res'):
            # res.append(i)
            for j in i.get('column'):
                res.append(j)
        # for z in res:
        #     res_list.append({
        #         'item_code': z.get('value'),
        #         'item_name': z.get('value'),
        #         'department': z.get('value'),
        #         'item_description': z.get('value'),
        #         'user': z.get('value'),
        #         'creatd_time': z.get('value'),
        #         })
        return res_list


class SourceUnitDetail(Resource):
    def get(self, id):
        res = []
        parser = reqparse.RequestParser()
        parser.add_argument('unit_name', type=str, location='args')
        args = parser.parse_args()

        args_dict = {}
        # if args.unit_name:
        #     args_dict['unit_name'] = args.unit_name
        items = ItemInformation.objects.filter(item_name=id)
        if items:
            for item in items:
                res.append({
                    "user": item.user,
                    "user_id": item.user_id,
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "item_code": item.item_code,
                    "item_depart": item.item_depart,
                    "item_description": item.item_description,
                    "create_date": str(item.create_date)
                })
        else:
            res = '查询结果不存在'

        return res


bench_api.add_resource(SourceUnitList, '/source_unit')
bench_api.add_resource(SourceUnitDetail, '/source_unit_detail/<id>')
