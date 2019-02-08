# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import six
import json

EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


def validate_string(x):
    return not x.isdigit()


def validate_numerical(x):
    if isinstance(x, int):
        return True
    if isinstance(x, six.string_types):
        return x.isdigit()
    return False


def validate_list(x):
    if isinstance(x, six.string_types):
        try:
            x = json.loads(x)
        except:
            return False
    try:
        list(x)
    except TypeError:
        return False
    return True


def validate_boolean(x):
    if isinstance(x, bool):
        return True
    if isinstance(x, six.string_types):
        if x.lower() in ["true", "false", "0", "1"]:
            return True
    if isinstance(x, int):
        # int should not be treated as boolean, but Python does, so we might as well
        if x == 0 or x == 1:
            return True
    return False


def validate_email(x):
    return isinstance(x, six.string_types) and EMAIL_REGEX.match(x)
