# -*- coding: utf-8 -*-

import sys
import datetime
import uuid
from flask import request
from flask_restful import reqparse, Api, Resource
from uop.permission import perm_blueprint
from uop.models import UserInfo,PermissionList,RoleInfo,Menu2_perm,Api_perm
from uop.permission.errors import perm_errors
from uop.log import Log
from uop.util import response_data,deal_enbedded_data

reload(sys)
sys.setdefaultencoding('utf-8')

perm_api = Api(perm_blueprint, errors=perm_errors)

class UserManage(Resource):
    """
    管理用户
    """
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, location='args')
        parser.add_argument('role', type=str, location='args')
        parser.add_argument('id', type=str, location='args')
        parser.add_argument('department', type=str, location='args')
        parser.add_argument('page_num', type=int, location='args')
        parser.add_argument('page_size', type=int, location='args')
        args = parser.parse_args()
        condition = {}
        data={}
        res_list=[]
        if args.username:
            condition["username"] = args.username
        if args.id:
            condition["id"] = args.id
        if args.role:
            condition["role"] = args.role
        if args.department:
            condition["department"] = args.department
        try:
            total_count = UserInfo.objects.filter(**condition).count()
            if args.page_num and args.page_size:
                skip_count = (args.page_num - 1) * args.page_size
                Users = UserInfo.objects.filter(**condition).order_by('-last_login_time').skip(skip_count).limit(args.page_size)
            else:
                Users=UserInfo.objects.filter(**condition).order_by('-last_login_time')
            for user in Users:
                res = {}
                res["id"] = user.id
                res["username"] = user.username
                res["role"] = user.role
                res["department"] = user.department
                res["updated_time"] = str(user.updated_time)
                res["last_login_time"] = str(user.last_login_time)
                res["created_time"] = str(user.created_time)
                res_list.append(res)
            data["total_count"] = total_count
            data["res_list"] = res_list
            code=200
            msg="Get user info success"
        except Exception as e:
            msg = "Get user info error,error msg is %s"  % str(e)
            Log.logger.error(msg)
            code=500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code


    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('role', type=str)
        parser.add_argument('id', type=str)
        parser.add_argument('department', type=str)
        args = parser.parse_args()
        try:
            user=UserInfo.objects.get(id=args.id)
            user.role = args.role
            user.department = args.department
            user.updated_time = datetime.datetime.now()
            user.save()
            code=200
            data = "Success"
            msg = "Update user info success"
        except Exception as e:
            msg = "Update user info error,error msg is %s"  % str(e)
            Log.logger.error(msg)
            code=500
            data= "Error"
        ret=response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str)
        args = parser.parse_args()
        try:
            user=UserInfo.objects.get(id=args.id)
            user.delete()
            code=200

            data="Success"
            msg="Delete user success"
        except Exception as e:
            msg = "Delete user error,error msg is %s"  % str(e)
            Log.logger.error(msg)
            code=500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

class PermManage(Resource):
    """
    管理权限
    """
    def get(self):
        pass

    def post(self):
        pass


class AllPermManage(Resource):
    """
    管理权限
    """
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, location='args')
        parser.add_argument('role', type=str, location='args')
        parser.add_argument('perm_type', type=str, location='args')
        args = parser.parse_args()
        condition = {}
        data={}
        res_list=[]
        if args.name:
            condition["name"] = args.name
        if args.role:
            condition["role"] = args.role
        if args.perm_type:
            condition["perm_type"] = args.perm_type
        try:
            Permissions = PermissionList.objects.filter(**condition)
            for permission in Permissions:
                res={}
                res["id"] = permission.id
                res["name"] = permission.name
                res["role"] = permission.role
                res["buttons"] = permission.buttons
                res["icons"] = permission.icons
                res["url"] = permission.url
                res["perm_type"] = permission.perm_type
                res["created_time"] = permission.created_time
                res["updated_time"] = permission.updated_time
                res["meau2_permission"] = deal_enbedded_data(permission.permission)
                res["api_permission"] = deal_enbedded_data(permission.api_permission)
                res_list.append(res)
            data["res_list"] = res_list
            code = 200
            msg = "Get permission info success"
        except Exception as e:
            msg = "Get permission info error,error msg is %s" % str(e)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('buttons', type=dict, location="json")
        parser.add_argument('icons', type=dict, location="json")
        parser.add_argument('url', type=str)
        parser.add_argument('perm_type', type=str)
        parser.add_argument('meau2_permission', type=list, location="json")
        parser.add_argument('api_permission', type=list, location="json")
        parser.add_argument('action', type=str,
                            choices=('create_meau_perm', 'create_meau2_perm', 'create_api_perm'),
                            required=True,
                            location='json')
        args = parser.parse_args()
        try:
            Permission=PermissionList(
                id = args.id,
                name = args.name,
                role = "super_admin",
                buttons = args.buttons,
                icons = args.icons,
                url = args.url,
                perm_type = args.perm_type
                )

            for meau2 in args.meau2_permission:
                id = meau2.get("id")
                name = meau2.get("name")
                url = meau2.get("url")
                parent_id = meau2.get("parent_id")
                meau2_perm_ins=Menu2_perm(id=id,name=name,url=url,parent_id=parent_id)
                Permission.menu2_permission.append(meau2_perm_ins)
            for api_perm in args.api_permission:
                id = api_perm.get("id")
                name = api_perm.get("name")
                endpoint = api_perm.get("endpoint")
                method = api_perm.get("method")
                api_perm_ins = Api_perm(id=id,name=name,endpoint=endpoint,method=method)
                Permission.api_permission.append(api_perm_ins)
            Permission.save()
            if args.action == "create_meau2_perm":
                Permission = PermissionList.objects.get(id=args.id)
                for meau2 in args.meau2_permission:
                    id = meau2.get("id")
                    name = meau2.get("name")
                    url = meau2.get("url")
                    parent_id = meau2.get("parent_id")
                    meau2_perm_ins = Menu2_perm(id=id, name=name, url=url, parent_id=parent_id)
                    Permission.menu2_permission.append(meau2_perm_ins)
                Permission.save()
            code = 200
            msg = "Create permission success"
            data = "Success"
        except Exception as e:
            code = 500
            msg = "Create permission error,error msg is %s" % str(e)
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('meau2_name', type=str)
        parser.add_argument('action', type=str,
                            choices=('dellete_meau_perm', 'delete_meau2_perm', 'delete_api_perm'),
                            required=True,
                            location='json')
        args = parser.parse_args()
        try:
            Permission = PermissionList.objects.get(name=args.name)
            if args.action in ["delete_meau_perm","delete_api_perm"]:
                Permission.delete()
            if args.action == "delete_meau2_perm":
                meau2_perms=Permission.menu2_permission
                delete_meau2_perms=[]
                for meau2 in meau2_perms:
                    meau2_name = meau2.get("name")
                    if meau2_name == args.meau2_name:
                        delete_meau2_perms.append(meau2)
                for delete_meau2 in delete_meau2_perms:
                    meau2_perms.remove(delete_meau2)
                Permission.save()
            code = 200
            msg = "Delete permission success"
            data = "Success"
        except Exception as e:
            msg = "Delete permission error,error msg is %s" % str(e)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('buttons', type=dict, location="json")
        parser.add_argument('icons', type=dict, location="json")
        parser.add_argument('url', type=str)
        parser.add_argument('perm_type', type=str)
        parser.add_argument('meau2_permission', type=list, location="json")
        parser.add_argument('api_permission', type=list, location="json")
        parser.add_argument('action', type=str,
                            choices=('update_meau_perm', 'update_meau2_perm', 'update_api_perm'),
                            required=True,
                            location='json')
        args = parser.parse_args()
        try:
            Permission = PermissionList.objects.get(name=args.name)
            if args.id:
                Permission.id = args.id
            if args.name:
                Permission.name = args.name
            if args.buttons:
                Permission.buttons = args.buttons
            if args.icons:
                Permission.icons = args.icons
            if args.url:
                Permission.url = args.url
            if args.perm_type:
                Permission.perm_type = args.perm_type
            if args.meau2_permission:
                pass
            if args.api_permission:
                pass

        except Exception as e:
            pass




class RoleManage(Resource):
    """
    管理角色
    """
    def get(self):
        data={}
        res_list=[]
        try:
            Roles=RoleInfo.objects.all()
            for role in Roles:
                res={}
                res["id"] = role.id
                res["name"] = role.name
                res["created_time"] = role.created_time
                res["description"] = role.description
                res_list.appned(res)
            data["res_list"] = res_list
            code = 200
            msg="Get role info success"
        except Exception as e:
            msg = "Get role info error,error msg is %s" % str(e)
            Log.logger.error(msg)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        args = parser.parse_args()
        try:
            id=str(uuid.uuid1())
            Role = RoleInfo(id=id,name=args.name,description=args.description,
                            created_time=datetime.datetime.now(),updated_time=datetime.datetime.now())
            Role.save()
            code = 200
            msg = "Create role success"
            data = "Success"
        except Exception as e:
            msg = "Create role error,error msg is %s" % str(e)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('new_name', type=str)
        parser.add_argument('description', type=str)
        args = parser.parse_args()
        try:
            Users = UserInfo.objects.filter(role=args.name)
            Role = RoleInfo.objects.get(name=args.name)
            if not Users:
                if args.new_name:
                    Role.name = args.new_name
                if args.description:
                    Role.description = args.description
            else:
                if args.description:
                    Role.description = args.description
                if args.name:
                    Role.name = args.new_name
                for user in Users:
                    user.role = args.new_name
                    user.save()
            code = 200
            msg = "Update role success"
            data = "Success"
        except Exception as e:
            msg = "Update role error, error msg is %s" % str(e)
            data = "Error"
            code = 500
        ret = response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()
        try:
            Users=UserInfo.objects.filter(role=args.name)
            Role = RoleInfo.objects.get(name=args.name)
            if not Users:
                Role.delete()
                code = 200
                msg = "Delete role success"
                data = "Success"
            else:
                code = 400
                msg = "Delete role failed.Some users are also part of this role"
                data="Failed"
        except Exception as e:
            msg = "Delete role error, error msg is %s" % str(e)
            data = "Error"
            code = 500
        ret = response_data(code, msg, data)
        return ret, code



perm_api.add_resource(UserManage, '/user')
perm_api.add_resource(PermManage, '/perm')
perm_api.add_resource(RoleManage, '/role')
perm_api.add_resource(AllPermManage, '/allperm')



