# -*- coding: utf-8 -*-
import datetime
from flask_mongoengine import MongoEngine
import datetime
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


class ComputeIns(db.EmbeddedDocument):
    ins_name = db.StringField(required=True)
    ins_id = db.StringField(required=True, unique=True)
    # ins_type = db.StringField(required=False)
    cpu = db.IntField(required=False)
    mem = db.IntField(required=False)
    # disk = db.StringField(required=False)
    # quantity = db.StringField(required=False, default_value='1')
    # version = db.StringField(required=False)
    url = db.StringField(required=False)
    meta = {
        'collection': 'compute_ins',


class ResComputeIns(db.EmbeddedDocument):
    username = db.StringField(required=True)
    password = db.StringField(required=True)
    ip = db.StringField(required=True)
    port = db.IntField()

    ins_name = db.StringField(required=True)
    ins_id = db.StringField(required=True, unique=True)
    cpu = db.IntField(required=False)
    mem = db.IntField(required=False)
    url = db.StringField(required=False)
    meta = {
        'collection': 'res_compute_ins',
>>>>>>> Stashed changes
        'index': [
            {
                'fields': ['ins_name', 'ins_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }


<<<<<<< Updated upstream
class DBIns(db.EmbeddedDocument):
=======
class ResDBIns(db.EmbeddedDocument):
    username = db.StringField(required=True)
    password = db.StringField(required=True)
    ip = db.StringField(required=True)
    port = db.StringField()

>>>>>>> Stashed changes
    ins_name = db.StringField(required=True)
    ins_id = db.StringField(required=True, unique=True)
    ins_type = db.StringField(required=False)
    cpu = db.IntField(required=False)
    mem = db.IntField(required=False)
    disk = db.IntField(required=False)
    quantity = db.IntField(required=False, default_value=0)
    version = db.StringField(required=False)
    meta = {
<<<<<<< Updated upstream
        'collection': 'db_ins',
=======
        'collection': 'res_db_ins',
>>>>>>> Stashed changes
        'index': [
            {
                'fields': ['ins_name', 'ins_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }


<<<<<<< Updated upstream
class ResourceModel(db.DynamicDocument):
=======
class ResResourceModel(db.DynamicDocument):
>>>>>>> Stashed changes
    resource_name = db.StringField(required=True, unique=True)
    project = db.StringField(required=True)
    department = db.StringField(required=True)
    department_id = db.StringField(required=True)
    res_id = db.StringField(required=True, unique=True)
    user_name = db.StringField(required=False)
    user_id = db.StringField(required=False)
<<<<<<< Updated upstream
    created_date = db.DateTimeField(default=datetime.datetime.now())
    domain = db.StringField(required=False)
    env = db.StringField(required=False)
    application_status = db.StringField(required=False)
    # approval_status = db.StringField(required=False)
    resource_list = db.ListField(db.EmbeddedDocumentField('DBIns'))
    compute_list = db.ListField(db.EmbeddedDocumentField('ComputeIns'))

    meta = {
        'collection': 'resources',
=======
    domain = db.StringField(required=False)
    env = db.StringField(required=False)
    application_status = db.StringField(required=False)
    resource_list = db.ListField(db.EmbeddedDocumentField('ResDBIns'))
    compute_list = db.ListField(db.EmbeddedDocumentField('ResComputeIns'))
    created_date = db.DateTimeField(default=datetime.datetime.now())

    meta = {
        'collection': 'res_resources',
>>>>>>> Stashed changes
        'index': [
            {
                'fields': ['resource_name', 'res_id'],
                'sparse': True,
                }
            ],
        'index_background': True
        }
<<<<<<< Updated upstream


class Approval(db.DynamicDocument):
    approval_id = db.StringField(required=True, max_length=50, unique=True)
    resource_id = db.StringField(required=True, unique=True)
    department_id = db.StringField(required=True)
    creator_id = db.StringField(required=True)
    create_date = db.DateTimeField(default=datetime.datetime.now)
    approve_uid = db.StringField(required=False)
    approve_date = db.DateTimeField(required=False)
    # processing/success/failed
    approval_status = db.StringField(required=True)
    annotation = db.StringField(max_length=50, required=False)
    meta = {
        'collection': 'approval',
        'index': [
            {
                'fields': ['resource_id', 'approval_status'],
                'sparse': True,
                }
            ],
        'index_background': True
    }
=======
>>>>>>> Stashed changes
