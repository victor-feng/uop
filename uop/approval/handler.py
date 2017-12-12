# -*- coding: utf-8 -*-
from uop.models import ComputeIns
from uop.log import Log


def attach_domain_ip(compute_list, res):
    old_compute_list = res.compute_list
    for c in compute_list:
        if not c.get("domain_ip", ""):
            return False
    try:
        for i in xrange(0, len(old_compute_list)):
            match_one = filter(lambda x: x["ins_id"] == old_compute_list[i].ins_id, compute_list)[0]
            old_compute_list.remove(old_compute_list[i])
            compute = ComputeIns(ins_name=match_one["ins_name"], ins_id=match_one["ins_id"],
                                        cpu=match_one["cpu"], mem=match_one["mem"],
                                        url=match_one["url"], domain=match_one["domain"],
                                        quantity=match_one["quantity"], port=match_one["port"],
                                        domain_ip=match_one["domain_ip"])
            old_compute_list.insert(i, compute)
        res.save()
    except Exception as e:
        Log.logger.error("attach domain_ip to compute error:{}".format(e))
    return True