# -*- coding: utf-8 -*-
import datetime

from flask_mongoengine import MongoEngine

db = MongoEngine()


class User(db.Document):
    email = db.StringField(required=True)
    first_name = db.StringField(max_length=50)
    last_name = db.StringField(max_length=50)



class UserInfo(db.Document):
    id = db.StringField(required=True, max_length=50, unique=True, primary_key=True)
    username = db.StringField(required=True, max_length=50)
    password = db.StringField(required=True, max_length=50)
    is_admin = db.BooleanField(required=False, default=False)

    meta = {
            "collection": "uop_userinfo",
            "index": [{
                'fields': ['username'],
                'unique': True,
                }]
            }


class Deployment(db.Document):
    deploy_id = db.StringField(max_length=100)
    deploy_name = db.StringField(max_length=50)
    initiator = db.StringField(max_length=50)
    project_name = db.StringField(max_length=50)
    created_time = db.DateTimeField(default=datetime.datetime.now())
    environment = db.StringField(max_length=50)
    exec_tag = db.StringField(max_length=50)
    exec_context = db.StringField(max_length=5000)
    app_image = db.StringField(max_length=100)
