# -*- coding: utf-8 -*-
import datetime
from uop.models import StatusRecord
from uop.log import Log

def get_deploy_status(deploy_id, deploy_type, res_type):
    try:
        docker_status_list = []
        s_type = '%s_%s' % (deploy_type, res_type)
        status_records = StatusRecord.objects.filter(deploy_id=deploy_id, s_type=s_type).order_by('created_time')
        for sr in status_records:
            docker_status_list.append(sr.status)
        for s_status in docker_status_list:
            if 'fail' in s_status:
                return False, len(docker_status_list)
        else:
            return True, len(docker_status_list)
    except Exception as e:
        Log.logger.error("[UOP] get_deploy_status failed, Excepton: %s" % str(e.args))


def create_status_record(resource_id, deploy_id, s_type, msg, status, set_flag, unique_flag=None):
    try:
        status_record = StatusRecord()
        status_record.res_id = resource_id
        status_record.deploy_id = deploy_id
        status_record.s_type = s_type
        status_record.set_flag = set_flag
        status_record.created_time = datetime.datetime.now()
        status_record.msg = msg
        status_record.status = status
        status_record.unique_flag = unique_flag
        status_record.save()
    except Exception as e:
        Log.logger.error("[UOP] create_status_record failed, Excepton: %s" % str(e.args))
