# -*- coding: utf-8 -*-
import json
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.res_callback import res_callback_blueprint
from uop.models import User
from uop.res_callback.errors import res_callback_errors
import requests
# from uop_backend.config import res_callback_url
res_callback_api = Api(res_callback_blueprint, errors=res_callback_errors)
res_callback_url = 'http://cmdb-test.syswin.com/cmdb/api/'


class UserRegister(Resource):
    """
    this is a test code
    """
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


class ResCallback(Resource):
    def post(self):
        data = {}
        parser = reqparse.RequestParser()
        parser.add_argument('resource_id', type=str, required=True)
        parser.add_argument('resource_name', type=str, required=True)
        parser.add_argument('under_id', type=str, required=True)
        parser.add_argument('domain', type=str)
        parser.add_argument('env', type=str)
        parser.add_argument('container', type=dict)
        parser.add_argument('db_info', type=dict)

        args = parser.parse_args()
        project_name = args.resource_name
        project_id = args.resource_id
        under_id = args.under_id
        domain = args.domain
        env = args.env
        container = args.container
        db_info = args.db_info
        data['resource_id'] = project_id
        data['resource_name'] = project_name
        data['under_id'] = under_id
        data['domain'] = domain
        data['container'] = container
        data['env'] = env
        data['db_info'] = db_info
        res = requests.post(res_callback_url + 'repo_store/', data=json.dumps(data))

        return res


res_callback_api.add_resource(UserRegister, '/users')
res_callback_api.add_resource(ResCallback, '/res')
