#!/usr/bin/env python
#coding:utf-8

from uop.log import Log
import jenkins


def jenkins_setting(jenkins_server_url,username,password):
    JenKins.server = jenkins.Jenkins(jenkins_server_url, username=username, password=password)


class JenKins(object):
    server = None

    @property
    def server(self):
        if JenKins.server is not None:
            return  JenKins.server
    @server.setter
    def server(self,value):
        if value is not None:
             JenKins.server = value


class JenkinsApi(object):

    @classmethod
    def get_job(cls,jenkins_server,job_name):
        try:
            pass
        except Exception as e:
            pass
