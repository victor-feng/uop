# -*- coding: utf-8 -*-
import sys
import ldap
reload(sys)
sys.setdefaultencoding('utf-8')
passwd = 'syswin1~'

ldap.set_option(ldap.OPT_REFERRALS, 0)    # 不加这个访问不到MS的服务
con = ldap.initialize('ldap://172.28.4.103:389')
con.simple_bind_s('crm_test1', 'syswin#')

base_dn = 'dc=syswin,dc=com'
scope = ldap.SCOPE_SUBTREE

input = sys.argv[1]

# filter = "(&(|(cn=*%(input)s*)(mail=*%(input)s*))(mail=*))" % {'input': input}
filter = "(&(|(cn=*%(input)s*)(sAMAccountName=*%(input)s*))(sAMAccountName=*))" % {'input': input}

# attrs = ['mail', 'givenName', 'sn', 'department', 'telephoneNumber', 'displayName']
attrs = ['sAMAccountName', 'mail', 'givenName', 'sn', 'department', 'telephoneNumber', 'displayName']

cn = None
result = []
for i in con.search_s(base_dn, scope, filter, None):
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
        cn = d.get('distinguishedName', '')
        print cn

print '共找到结果 %s 条' % (len(result))
for d in result:
    # print '%(mail)s\t%(sn)s%(givenName)s\t%(telephoneNumber)s %(department)s' %d
    print '%(sAMAccountName)s\t%(mail)s\t%(sn)s%(givenName)s\t%(mobile)s %(department)s' %d


def verify_user(passwd):
    try:
        if con.simple_bind_s(cn, passwd):
            print '验证成功'
        else:
            print '验证失败'
    except ldap.INVALID_CREDENTIALS, e:
        print e


verify_user(passwd)
