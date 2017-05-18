# -*- coding: utf-8 -*-
import json
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from mongoengine import NotUniqueError
from uop.auth import auth_blueprint
from uop.models import UserInfo, User
from uop.auth.errors import user_errors
from wtforms import ValidationError
import ldap3


auth_api = Api(auth_blueprint, errors=user_errors)


class UserRegister(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        args = parser.parse_args()

        id = args.id
        username = args.username
        password = args.password

        try:
            UserInfo(id=id, username=username, password=password).save()
            code = 200
            res = '注册成功'
        except NotUniqueError:
            code = 501
            res = '用户名已经存在'

        res = {
            "code": code,
            "result": {
                "res": res,
                "msg": "test info"
                }
        }
        return res, code

    def get(self):
        return "test info", 200


class UserLogin(Resource):
    def post(self):
        host = '172.28.4.103'
        port = 389
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str)
        parser.add_argument('password')
        args = parser.parse_args()

        username = args.username
        password = args.password
        server = ldap3.Server(host, port, get_info=ldap3.ALL)
        conn = None
        auto_bind = False
        try:
            if username:
                username = '%s' % username
                if password:
                    auto_bind = True
            conn = ldap3.Connection(
                    server,
                    user=username,
                    password=password,
                    auto_bind=auto_bind,
                    authentication=ldap3.NTLM
                    )
            if not auto_bind:
                succ = conn.bind()
            else:
                succ = True
            msg = conn.result
            conn.unbind()
            return succ, msg
        except Exception as e:
            if conn:
                conn.unbind()
            return False, e


class UserList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        args = parser.parse_args()

        username = args.username
        password = args.password
        user = UserInfo.objects.get(username=username)
        if user:
            if user.password == password:
                res = '登录成功'
                code = 200
            else:
                res = '密码错误'
                code = 304
        else:
            code = 305
            res = '用户不存在'
        res = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": ""
                    }
                }
        return res, code


class AdminUserList(Resource):
    def post(self):
        data = json.loads(request.body)
        id = data.get('id')
        password = data.get('password')
        user = UserInfo.objects.get(id=id)
        if user:
            if user.password == password:
                if user.is_admin:
                    res = '管理员登录成功'
                    code = 200
                else:
                    res = '您没有管理员权限'
                    code = 405
        else:
            res = '用户不存在'
            code = 404
        res = {
                'code': code,
                'result': {
                    'res': res,
                    'msg': ''
                    }
                }
        return json.dumps(res)


class AdminUserDetail(Resource):
    def put(self, name):
        user = UserInfo.objects.get(username=name)
        is_admin = json.loads(request.body())
        if user:
            user.is_admin = is_admin
            user.save()

    def delete(self, name):
        user = UserInfo.objects.get(username=name)
        user.delete()
        code = 200
        res = '删除用户成功'
        res = {
                'code': code,
                'result': {
                    'res': res,
                    'msg': ''
                    }
                }
        return res, 200


class AllUserList(Resource):
    def get(self):
        all_user = []
        users = UserInfo.objects.all()
        for i in users:
            all_user.append(i.username)
        return all_user


# admin user
auth_api.add_resource(AdminUserList, '/adminlist')
auth_api.add_resource(AdminUserDetail, '/admindetail/<name>')
# common user
auth_api.add_resource(UserRegister, '/users')
auth_api.add_resource(UserLogin, '/userdetail')
auth_api.add_resource(UserList, '/userlist')
auth_api.add_resource(AllUserList, '/all_user')
