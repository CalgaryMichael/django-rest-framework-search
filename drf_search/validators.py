# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six
import json


def validate_numerical(x):
    if isinstance(x, int):
        return True
    if isinstance(x, six.string_types):
        return x.isdigit()
    return False


def validate_list(x):
    if isinstance(x, list):
        return True
    if isinstance(x, six.string_types):
        try:
            x = json.loads(x)
            if isinstance(x, list):
                return True
        except:
            return False
    return False
