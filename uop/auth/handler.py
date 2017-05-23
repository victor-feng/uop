# -*- coding: utf-8 -*-
import json
import sys
import ldap
import datetime
import os
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from mongoengine import NotUniqueError
from uop.auth import auth_blueprint
from uop.models import UserInfo, User
from uop.auth.errors import user_errors
from wtforms import ValidationError
reload(sys)
sys.setdefaultencoding('utf-8')
base_dn = 'dc=syswin,dc=com'
scope = ldap.SCOPE_SUBTREE
ldap_server = 'ldap://172.28.4.103:389'
username = 'crm_test1'
passwd_admin = 'syswin#'

auth_api = Api(auth_blueprint, errors=user_errors)


class LdapConn(object):
    def __init__(self, server, admin_name, admin_pass, base_dn, scope, flag=None, cn=None):
        self.server = server,
        self.name = admin_name,
        self.passwd = admin_pass,
        self.base_dn = base_dn,
        self.scope = scope,
        self.flag = flag,

    def conn_ldap(self):
        ldap.set_option(ldap.OPT_REFERRALS, 0)
        conn = ldap.initialize(self.server[0])
        conn.simple_bind_s(self.name[0], self.passwd[0])
        return conn

    def verify_user(self, id, password):
        result = []
        con = self.conn_ldap()
        filter_field = "(&(|(cn=*%(input)s*)(sAMAccountName=*%(input)s*))(sAMAccountName=*))" % {'input': id}
        attrs = ['sAMAccountName', 'mail', 'givenName', 'sn', 'department', 'telephoneNumber', 'displayName']
        for i in con.search_s(base_dn, scope, filter_field, None):
            if i[0]:
                d = {}
                for k in i[1]:
                    d[k] = i[1][k][0]
                if 'telephoneNumber' not in d:
                    d['telephoneNumber'] = '(无电话)'
                if 'department' not in d:
                    d['department'] = '(无部门)'
                if 'sn' not in d and 'givenName' not in d:
                    d['givenName'] = d.get('displayName', '')
                if 'sn' not in d:
                    d['sn'] = ''
                if 'givenName' not in d:
                    d['givenName'] = ''
                result.append(d)
                self.cn = d.get('distinguishedName', '')
                print self.cn
                id = d.get('sAMAccountName', '')
                mail = d.get('mail', '')
                name = d.get('cn', '')
                mobile = d.get('mobile', '')
                department = d.get('department', '')
                field_value = {
                        'id': id,
                        'mail': mail,
                        'name': name,
                        'mobile': mobile,
                        'department': department
                        }
                print d
        print '共找到结果 %s 条' % (len(result))
        for d in result:
            print '%(sAMAccountName)s\t%(mail)s\t%(sn)s%(givenName)s\t%(mobile)s %(department)s' % d
        try:
            if con.simple_bind_s(self.cn, password):
                print 'verify successfully'
                self.flag = 1
            else:
                print 'verify fail'
                self.flag = 0
        except ldap.INVALID_CREDENTIALS, e:
            print e
            self.flag = 0
        return self.flag, field_value


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


class UserList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str)
        parser.add_argument('password', type=str)
        args = parser.parse_args()

        id = args.id
        password = args.password
        conn = LdapConn(ldap_server, username, passwd_admin, base_dn, scope)
        verify_code, verify_res = conn.verify_user(id, password)

        verify_res_name = verify_res.get('name')  # 获取到用户名
        verify_res_department = verify_res.get('department')  # 获取到部门
        user = verify_res_name.decode('utf-8')
        department = verify_res_department.decode('utf-8')
        user_id = verify_res.get('id')  # 获取到工号
        is_admin = False

        if verify_code:
            res = '登录成功'
            code = 200
            try:
                user = UserInfo.objects.get(id=user_id)
                is_admin = user.is_admin
            except UserInfo.DoesNotExist:
                user_obj = UserInfo()
                user_obj.id = user_id
                user_obj.username = user
                user_obj.password = password
                user_obj.department = department
                user_obj.created_time = datetime.datetime.now()
                user_obj.save()
            msg = {
                    'user_id': user_id,
                    'username': user,
                    'department': department,
                    'is_admin': is_admin
                    }
        else:
            res = '登录失败'
            code = 304
            msg = ''
        # try:
        #     user = UserInfo.objects.get(id=user_id)
        # except UserInfo.DoesNotExist:
        #     user_obj = UserInfo()
        #     user_obj.id = user_id
        #     user_obj.username = user
        #     user_obj.password = password
        #     user_obj.department = department
        #     user_obj.save()

        res = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                    }
                }
        return json.dumps(res)


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
    def put(self, tag):
        user = UserInfo.objects.get(username=tag)
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
            data = {
                    'id': i.id,
                    'username': i.username,
                    'department': i.department,
                    'is_admin': i.is_admin,
                    'created_time': str(i.created_time)
                    }
            all_user.append(data)
        return all_user


# admin user
auth_api.add_resource(AdminUserList, '/adminlist')
auth_api.add_resource(AdminUserDetail, '/admindetail/<tag>')
# common user
auth_api.add_resource(UserRegister, '/users')
auth_api.add_resource(UserList, '/userlist')
auth_api.add_resource(AllUserList, '/all_user')


if __name__ == "__main__":
    conn = LdapConn()
    conn.verify_user(147749, 'syswin1~')
