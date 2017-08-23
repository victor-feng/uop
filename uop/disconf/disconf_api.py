# -*- coding: utf-8 -*-

import requests
import json
import os
import shutil
#from uop import models
from config import APP_ENV, configs


#DISCONF_URL = 'http://172.28.11.111:8081'
DISCONF_URL = configs[APP_ENV].DISCONF_URL
DISCONF_USER_INFO = configs[APP_ENV].DISCONF_USER_INFO
SIGNIN = DISCONF_URL + '/api/account/signin'
SESSION = DISCONF_URL + '/api/account/session'
APP = DISCONF_URL + '/api/app'
FILETEXT = DISCONF_URL + '/api/web/config/filetext'
FILE = DISCONF_URL + '/api/web/config/file'
APP_LIST = DISCONF_URL + '/api/app/list'
ENV_LIST = DISCONF_URL + '/api/env/list'
VERSION_LIST = DISCONF_URL + '/api/web/config/versionlist'
CONFIG_LIST = DISCONF_URL + '/api/web/config/list'
CONFIG_SHOW = DISCONF_URL + '/api/web/config'
CONFIG_DEL = DISCONF_URL + '/api/web/config'
session = requests.Session()


class ServerError(Exception):
    pass


def exchange_disconf_name(name):
    disconf_with_uuid = name
    disconf_no_uuid = disconf_with_uuid.split('_')[:-2]




def disconf_signin():
    user_info = DISCONF_USER_INFO
    try:
        rep = requests.post(SIGNIN, data=user_info)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json


def disconf_session():
    user_info = DISCONF_USER_INFO
    try:
        res = session.post(SIGNIN, data=user_info)
        ret_json = json.loads(res.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json


def disconf_app(app_name, desc):
    app_info = {'app': app_name, 'desc': desc, 'emails': ''}
    try:
        disconf_session()
        rep = session.post(APP, data=app_info)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json


def disconf_file(appId, envId, version, myfilerar):
    try:
        file_content = {
                    'appId': (None,str(appId)),
                    'envId': (None,str(envId)),
                    'version': (None,str(version)),
                    'myfilerar': open(myfilerar,'rb')
                    }

        disconf_session()
        rep = session.post(FILE, files=file_content)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json


def disconf_filetext(appId, envId, version, fileContent, fileName):
    try:
        filetext = {
                    'appId': appId,
                    'envId': envId,
                    'version': version,
                    'fileContent': fileContent,
                    'fileName': fileName
                    }
        disconf_session()
        rep = session.post(FILETEXT, data=filetext)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json


def disconf_filetext_update(config_id, filecontent):
    try:
        url = '{filetext}/{config_id}'.format(filetext=FILETEXT, config_id=config_id)
        filetext = {
                    'fileContent': filecontent
                    }
        disconf_session()
        rep = session.put(url, data=filetext)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json


def disconf_filetext_delete(config_id):
    try:
        url = '{config_del}/{config_id}'.format(config_del=CONFIG_DEL, config_id=config_id)
        disconf_session()
        rep = session.delete(url)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return ret_json



def disconf_app_list():
    try:
        disconf_session()
        rep = session.get(APP_LIST)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')
        app_list = ret_json.get('page').get('result')

        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return app_list



def disconf_app_id(app_name):
    try:
        app_id = None
        disconf_session()
        app_list = disconf_app_list()
        for name in app_list:
            # name.get('name') is unicode
            if name.get('name') == app_name:
                # app_id is instance of int
                app_id = name.get('id')
                break
    except ServerError as e:
        raise ServerError(e.message)
    return app_id


def disconf_env_list():
    try:
        disconf_session()
        rep = session.get(ENV_LIST)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')
        env_list = ret_json.get('page').get('result')
        if result != 'true':
            message = 'ERROR:{result}'.format(result=ret_json)
            raise ServerError(message)

    except Exception as e:
        raise ServerError(e.message)
    return env_list


def disconf_env_id(env_name):
    try:
        env_id = None
        disconf_session()
        env_list = disconf_env_list()
        if env_list:
            for env in env_list:
                if env.get('name') == env_name:
                    env_id = env.get('id')
                    break
    except Exception as e:
        raise ServerError(e.message)
    return env_id


def disconf_env_name(env_id):
    try:
        env_name = None
        if (env_id is None) or (len(env_id) == 0):
            return ""

        disconf_session()
        env_list = disconf_env_list()
        if env_list:
            for env in env_list:
                if env.get('id') == int(env_id):
                    env_name = env.get('name')
                    break
    except Exception as e:
        raise ServerError(e.message)
    return env_name


def disconf_version_list(app_id):
    try:
        url = '{version_list}?appId={app_id}'.format(version_list=VERSION_LIST, app_id=app_id)
        disconf_session()
        rep = session.get(url)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result == 'true':
            result_list = ret_json.get('page').get('result')
            if result_list:
                version_id = ret_json.get('page').get('result')[0]
            else:
                version_id = None
        else:
            version_id = None

    except Exception as e:
        raise ServerError(e.message)
    return version_id


def disconf_config_list(app_id, env_id, version): ##config可以为空[]
    try:
        url = '{config_list}?appId={app_id}&envId={env_id}&version={version}&'.format(
                config_list=CONFIG_LIST, app_id=app_id, env_id=env_id, version=version)
        disconf_session()
        rep = session.get(url)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')

        if result == 'true':
            config_list = ret_json.get('page').get('result')
        else:
            config_list = []

    except Exception as e:
        raise ServerError(e.message)
    return config_list

def disconf_config_id_list(app_id, env_id, version):
    try:
        config_list = disconf_config_list(app_id, env_id, version)
        config_id_list = []
        if config_list:
            for config in config_list:
                config_id_list.append(config.get('configId'))
    except Exception as e:
        raise ServerError(e.message)
    return config_id_list


def disconf_config_id(app_id, env_id, config_name, version):
    try:
        config_id = None
        config_list = disconf_config_list(app_id, env_id, version)
        if config_list:
            for config in config_list:
                if config.get('key') == config_name:
                        config_id = config.get('configId')
                        break
    except Exception as e:
        raise ServerError(e.message)
    return config_id


def disconf_config_name_list(app_id, env_id, version):
    try:
        config_list = disconf_config_list(app_id, env_id, version)
        config_name_list = []
        if config_list:
            for config in config_list:
                config_name_list.append(config.get('key'))
    except Exception as e:
        raise ServerError(e.message)
    return config_name_list


def disconf_config_show(config_id):
    try:
        url = '{config_show}/{config_id}'.format(config_show=CONFIG_SHOW, config_id=config_id)
        disconf_session()
        rep = session.get(url)
        ret_json = json.loads(rep.text)
        result = ret_json.get('success')
        if result == 'true':
            config = ret_json.get('result')
        else:
            config = None
    except Exception as e:
        raise ServerError(e.message)
    return config


def disconf_add_app_config_api_content(app_name, filename, filecontent, version, env_id):
    try:
        app_id = disconf_app_id(app_name)
        if app_id is None:
            app_desc = '{res_name} config generated.'.format(res_name=app_name)
            disconf_app(app_name, app_desc)
            app_id = disconf_app_id(app_name)

        config_id = disconf_config_id(app_id=app_id, env_id=env_id, config_name=filename,version=version)
        if config_id is None:
            ret = disconf_filetext(app_id, env_id, version, fileContent=filecontent, fileName=filename)
        else:
            disconf_filetext_delete(config_id)
            ret = disconf_filetext(app_id, env_id, version, fileContent=filecontent, fileName=filename)
        result = 'success'
        message = 'instance_name:{ins_name},filename:{filename} success'.format(ins_name=app_name,filename=filename)
    except Exception as e:
        result = 'fail'
        message = e.message
    return result,message


def disconf_add_app_config_api_file(app_name, filename, myfilerar, version, env_id):
    try:
        app_id = disconf_app_id(app_name)
        if app_id is None:
            app_desc = '{res_name} config generated.'.format(res_name=app_name)
            disconf_app(app_name, app_desc)
            app_id = disconf_app_id(app_name)

        config_id = disconf_config_id(app_id=app_id, env_id=env_id, config_name=filename,version=version)
        if config_id is None:
            ret = disconf_file(app_id, env_id, version, myfilerar)
        else:
            disconf_filetext_delete(config_id)
            ret = disconf_file(app_id, env_id, version, myfilerar)

        result = 'success'
        message = 'instance_name:{ins_name},filename:{filename} success'.format(ins_name=app_name,filename=filename)
    except Exception as e:
        result = 'fail'
        message = e.message
    return result,message

def disconf_get_app_config_api(app_name, env_id):
    try:
        app_id = disconf_app_id(app_name=app_name)
        version_id = disconf_version_list(app_id=app_id)
        config_id_list = disconf_config_id_list(app_id=app_id, env_id=env_id, version=version_id)

        configurations = []
        for config_id in config_id_list:
            config = disconf_config_show(config_id)
            config_value = {}
            if config is not None:
                config_value['filename'] = config.get('key')
                config_value['filecontent'] = config.get('value')
                config_value['config_id'] = config.get('configId')
                configurations.append(config_value)
    except Exception as e:
        raise ServerError(e.message)
    return configurations


if __name__ == '__main__':
    version = "1_0_0"
    app_name = 'final70'
    env_id = '1'
    filename = 'test2'
    filecontent = 'dsfsdfsfs-new-add'
    myfilerar = '/root/test2'
    #print disconf_app_list()
    #print disconf_env_list()
    #print disconf_version_list(app_id=70)
    #print disconf_env_id('rd')
    #print disconf_env_name(env_id="")
    #print disconf_add_app_config_api_content(app_name, filename, filecontent, version='0_0_0_1', env_id='1')
    #print disconf_add_app_config_api_file(app_name, filename, myfilerar)
    #print disconf_get_app_config_api(app_name, env_id)
