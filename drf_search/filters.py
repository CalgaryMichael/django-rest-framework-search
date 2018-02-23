# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import operator
import rest_framework.filters
import rest_framework.compat
from django.db.models import Q
from collections import OrderedDict
from .fields import SearchField


class SearchFilterMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs["_search_fields"] = cls._get_search_fields(bases, attrs)
        attrs["_default_search_fields"] = cls._get_default_search_fields(attrs["_search_fields"])
        return super(SearchFilterMetaclass, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def _get_search_fields(cls, bases, attrs):
        fields = list()
        for field_name, obj in list(attrs.items()):
            if isinstance(obj, SearchField):
                fields.append((field_name, obj))
                for alias in obj.aliases:
                    if alias not in list(name for name, _ in fields):
                        fields.append((alias, obj))

        # allow for subclassing
        for base in reversed(bases):
            base_fields = list()
            if hasattr(base, "_search_fields"):
                for field_name, obj in base._search_fields:
                    if field_name not in attrs:
                        base_fields.append((field_name, obj))
                    for alias in obj.aliases:
                        field_names = (name for name, _ in fields)
                        base_field_names = (name for name, _ in base_fields)
                        if alias not in list(field_name) and alias not in list(base_fields):
                            base_fields.append((alias, obj))
                fields = base_fields + fields
        return OrderedDict(fields)

    @classmethod
    def _get_default_search_fields(cls, search_fields):
        return list(
            (field_name, field) for field_name, field
            in search_fields
            if field.default is True)
