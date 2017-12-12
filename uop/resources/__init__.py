# -*- coding: utf-8 -*-
from flask import Blueprint

resources_blueprint = Blueprint('resources_blueprint', __name__)

from . import handler, forms, errors, view
