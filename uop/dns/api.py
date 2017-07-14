import json
import sys
import os
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.inventory import Inventory
from ansible.runner import Runner
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils

dns_env = {'develop': '172.28.5.21', 'test': '172.28.18.212'}
config_file_path = '/root/dns/%s/usr/local/dns/systoon.com.zone' % ('172.28.20.124')
response = {'success': False, 'error': ''}


class ServerError(Exception):
    pass


class ConfigFile(object):
    def __init__(self, path_file):
        self.file = path_file

    def config_list(self):
        my_file = self.file
        with open(my_file, 'r+') as f:
            for line in f.readlines():
                print line

    def config_query(self, **kwargs):
        my_file = self.file
        name = kwargs.get('name')
        ip = kwargs.get('ip')
        args = name if name else ip
        rest = []
        try:
            with open(my_file, 'r+') as f:
                for line in f.readlines():
                    if args in line:
                        rest.append(args)
            return rest
        except Exception as exc:
            raise ServerError(exc)

    def config_update(self, name, ip):
        my_file = self.file
        cord = '%s IN A %s' % (name, ip)
        with open(my_file, 'w+') as f:
            f.write(cord)

    def config_add(self, **kwargs):
        my_file = self.file
        name = kwargs.get('name')
        ip = kwargs.get('ip')
        if (name is None) or (len(name) == 0):
            raise ServerError(u'name is not none or empty!')
        elif (ip is None) or (len(ip) == 0):
            raise ServerError(u'ip is not none or empty!')
        else:
            record = "%s        IN        A        %s\n" % (name, ip)
            print record
        try:
            file_content = open(my_file, 'r+').readlines()
            file_content.append(record)
            for line in file_content:
                if len(line) <= 1:
                    file_content.remove(line)
            content_to_str = "".join(file_content)
            with open(my_file, 'w+') as f:
                f.write(content_to_str)
        except Exception as exc:
            raise ServerError(exc)

    def config_delete(self, *args):
        pass


class AnsibleConnect(object):
    def __init__(self, env):
        self.env = env
        ip = dns_env.get(env)
        self.inventory = Inventory(['172.28.20.124'])

    def command(self, module_name='command', module_args='uname -a', timeout=10):
        try:
            command_runner = Runner(
                            module_name=module_name,
                            module_args=module_args,
                            timeout=timeout,
                            inventory=self.inventory,
                            private_key_file='/root/.ssh/id_rsa'
                            )
            res = command_runner.run()
            result = res.get('dark')
            if len(result) == 0:
                raise ServerError("ansible copy file error")
            else:
                response['success'] = True
            return response
        except Exception as exc:
            raise ServerError(exc)

    def copy_file(self, module_name='copy', module_args='src=%s dest=/usr/local/dns/systoon.com.zone backup=yes' % (config_file_path), timeout=10):

        response = {'success': False, 'error': ''}
        try:
            command_runner = Runner(
                            module_name=module_name,
                            module_args=module_args,
                            timeout=timeout,
                            inventory=self.inventory
                            )
            res = command_runner.run()
            #print res
            result = res.get('dark')
            if len(result) == 0:
                response['success'] = True
            else:
                response['success'] = False
        except Exception as exc:
            response['success'] = False
        return response

    def fetch_file(self, module_name='fetch', module_args='src=/usr/local/dns/systoon.com.zone dest=/root/dns/', timeout=10):
        try:
            command_runner = Runner(
                            module_name=module_name,
                            module_args=module_args,
                            timeout=timeout,
                            inventory=self.inventory
                            )
            res = command_runner.run()
            #print res
            result = res.get('dark')
            if len(result) == 0:
                response['success'] = True
            else:
                response['success'] = False
        except Exception as exc:
            response['success'] = False
        return response


class Dns(object):
    def __init__(self):
        pass

    @staticmethod
    def dns_add(env, domain):
        ip = dns_env[env]
        open_config_file = ConfigFile(config_file_path)
        open_config_file.config_add(name=domain, ip=ip)

    def dns_update(self, env, domain):
        pass

    def dns_query(self, **kwargs):
        pass

    def dns_delete(self, **kwargs):
        pass


if __name__ == '__main__':
    to_ansi = AnsibleConnect('172.28.20.124')
    to_ansi.command()
    '''
    fetch_result = to_ansi.fetch_file()
    if fetch_result['success']:
        Dns.dns_add('test', 'www.qita.com')
    copy_result = to_ansi.copy_file()
    if copy_result['success']:
        print "success"
    '''
