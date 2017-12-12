# -*- coding: utf-8 -*-
from flask import Blueprint

iteminfo_blueprint = Blueprint('iteminfo_blueprint', __name__)

from . import handler, forms, errors, view
