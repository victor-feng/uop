# -*- coding: utf-8 -*-
from flask import Flask, redirect
from flask_restful import Resource, Api
from config import configs
from models import db
from uop.user import user_blueprint
from uop.auth import auth_blueprint


def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(configs[config_name])
    db.init_app(app)

    @app.route('/docs')
    def docs():
        return redirect('/static/docs/index.html')

    # blueprint
    app.register_blueprint(user_blueprint, url_prefix='/api/user')
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')

    return app
