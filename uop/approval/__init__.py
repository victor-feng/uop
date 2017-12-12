# -*- coding: utf-8 -*-
from flask import Blueprint

approval_blueprint = Blueprint('approval_blueprint', __name__)

from . import handler, errors, view
