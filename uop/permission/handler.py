# -*- coding: utf-8 -*-


from flask import jsonify
from uop.models import PermissionList,RoleInfo,UserInfo



class ApiPermException(Exception):
    pass


method_dict={
    "0":False,
    "1":True
}


def get_api_permission():
    """
    #获取角色API权限
    :return:
    """
    try:
        api_all_perm={}
        Roles=RoleInfo.objects.all()
        for Role in Roles:
            api_role_perm={}
            api_endpoint_perm={}
            Permissions=PermissionList.objects.filter(perm_type="api",role=Role.name)
            for permission in Permissions:
                api_method_perm={}
                role=permission.role
                endpoint=permission.endpoint
                api_get=permission.api_get
                api_post=permission.api_post
                api_put=permission.api_put
                api_delete=permission.api_delete
                api_method_perm["GET"] = api_get
                api_method_perm["POST"] = api_post
                api_method_perm["PUT"] = api_put
                api_method_perm["DELETE"] = api_delete
                api_endpoint_perm[endpoint] = api_method_perm
                api_role_perm[role] = api_endpoint_perm
            #将全新加入到api_all_perm所有权限
            api_all_perm = dict(api_all_perm,** api_role_perm)
        return api_all_perm
    except Exception as e:
        err_msg = "Get api permission error,error msg is %s" % str(e)
        raise ApiPermException(err_msg)


def get_role(user_id):
    try:
        User = UserInfo.objects.get(id=user_id)
        role = User.role
        return role
    except Exception as e:
        err_msg = "Get role error,error msg is %s" % str(e)
        raise ApiPermException(err_msg)

