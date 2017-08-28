# -*- coding: utf-8 -*-

from flask import current_app


def get_CRP_url(env=None):
    if env:
        CPR_URL = current_app.config['CRP_URL'][env]
    else:
        CPR_URL = current_app.config['CRP_URL']['dev']
    return CPR_URL