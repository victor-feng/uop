# -*- coding:utf-8 -*-
import sys
import ldap
LDAP_HOST = '172.28.4.103'
LDAP_PORT = 389
USER = 'cn=crm_test1,dc=syswin,dc=com'
PASSWORD = 'syswin#'
BASE_DN = 'ou="思源集团",dc=syswin,dc=com'
ldap.set_option(ldap.OPT_REFERRALS, 0)
l = ldap.initialize('ldap://172.28.4.103:389')
l.set_option(ldap.OPT_REFERRALS, 0)


class LDAPTool:

    def __init__(self, ldap_host=None, base_dn=None, user=None, password=None):
        if not ldap_host:
            ldap_host = LDAP_HOST
        if not base_dn:
            self.base_dn = BASE_DN
        if not user:
            user = USER
        if not password:
            password = PASSWORD
        try:
            self.ldapconn = ldap.open(ldap_host)
            self.ldapconn.simple_bind(user, password)
            self.ldapconn.set_option(ldap.OPT_REFERRALS, 0)
        except ldap.LDAPError, e:
            print e

    # 根据表单提交的用户名，检索该用户的dn,一条dn就相当于数据库里的一条记录。
    # 在ldap里类似cn=username,ou=users,dc=gccmx,dc=cn,验证用户密码，必须先检索出该DN
    def ldap_search_dn(self, uid=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = None
        searchFilter = "cn=" + uid

        try:
            ldap_result_id = obj.search(self.base_dn, searchScope, searchFilter, retrieveAttributes)
            result_type, result_data = obj.result(ldap_result_id, 0)
            # 返回数据格式
            # ('cn=django,ou=users,dc=gccmx,dc=cn',
            #    {  'objectClass': ['inetOrgPerson', 'top'],
            #        'userPassword': ['{MD5}lueSGJZetyySpUndWjMBEg=='],
            #        'cn': ['django'], 'sn': ['django']  }  )
            #
            if result_type == ldap.RES_SEARCH_ENTRY:
                # dn = result[0][0]
                return result_data[0][0]
            else:
                return None
        except ldap.LDAPError, e:
            print e


if __name__ == '__main__':
    user = '147749'
    password = 'syswin1~'
    l = LDAPTool(user=user, password=password)
    # l.set_option(ldap.OPT_REFERRALS, 0)
    l.ldap_search_dn(uid=user)
