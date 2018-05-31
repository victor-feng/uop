# -*- coding: utf-8 -*-
import math
from flask_restful import abort

def pagination_calc_page(per_page, page, count):
    if per_page <= 0:
        abort(400, code=1000, message={'per_page': 'per_page must greater than 0'})
    record_count = count
    if record_count == 0:
        record_count = 1
    total_pages = int(math.ceil(record_count / float(per_page)))
    if page <= 0:
        page = total_pages
    return page, total_pages


def pagination_query(page, per_page, query):
    """
    转换为分页结果
    :param per_page: per page count
    :param page: page index
    :param query: query
    :return:
    """
    __import__('ipdb').set_trace()
    count = query.count()
    page, total_pages = pagination_calc_page(per_page, page, count)
    pagination = query.paginate(page, per_page)
    return {
        'total_pages': total_pages,
        'page': page,
        'per_page': per_page,
        'total_count': count,
        'objects': pagination.items
    }


