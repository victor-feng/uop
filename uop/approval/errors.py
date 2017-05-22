# -*- coding: utf-8 -*-
approval_errors = {
    'UserAlreadyExistsError': {
        'message': "A user with that username already exists.",
        'status': 409,
    },
    'ResourceDoesNotExist': {
        'message': "A resource with that ID no longer exists.",
        'status': 410,
        'extra': "Any extra information you want.",
    },
}

#reservation_errors = {
#    'ApprovalIsProcessing': {
#        "code": 400,
#        "result": {
#            "res": "failed",
#            "msg": ""
#        }
#    },
#    'ResourceDoesNotExist': {
#        'message': "A resource with that ID no longer exists.",
#        'status': 410,
#        'extra': "Any extra information you want.",
#    },
#}
