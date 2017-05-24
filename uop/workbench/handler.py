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


class UserRegister(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str)
        parser.add_argument('first_name', type=str)
        parser.add_argument('last_name', type=str)
        args = parser.parse_args()

        email = args.email
        first_name = args.first_name
        last_name = args.first_name

        User(email=email, first_name=first_name, last_name=last_name).save()

        res = {
            "code": 200,
            "result": {
                "res": "success",
                "msg": "test info"
            }
        }
        return res, 200

    @classmethod
    def get(cls):
        return "test info", 409


class SourceUnitList(Resource):
    def get(self):
        r = requests.get(url)
        return r.text


class SourceUnitDetail(Resource):
    def get(self):
        res = []
        parser = reqparse.RequestParser()
        parser.add_argument('unit_name', type=str, location='args')
        args = parser.parse_args()

        args_dict = {}
        if args.unit_name:
            args_dict['unit_name'] = args.unit_name
        items = ItemInformation.objects.filter(**args_dict)
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
        return res


bench_api.add_resource(SourceUnitList, '/source_unit')
bench_api.add_resource(SourceUnitDetail, '/source_unit_detail')
