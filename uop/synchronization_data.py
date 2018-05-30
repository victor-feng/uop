# -*- coding: utf-8 -*-
from models import ItemInformation
import mongoengine
mongoengine.connect(
    'uop',
    host='172.28.20.124',  # 根据环境变动
    port=27017,
    username='uop',
    password='uop'
)


def sync_data():
    items = ItemInformation.objects.filter(item_code="project")
    for item in items:
        item.cmdb2_project_id = item.item_id
        item.save()

if __name__ == '__main__':
    sync_data()


