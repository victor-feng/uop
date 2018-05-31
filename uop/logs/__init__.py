# -*- coding: utf-8 -*-
from flask import Blueprint

logs_blueprint = Blueprint('logs_blueprint', __name__)

from . import handler, errors, view
