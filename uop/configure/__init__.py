# -*- coding: utf-8 -*-
from flask import Blueprint

configure_blueprint = Blueprint('configure_blueprint', __name__)

from . import handler
