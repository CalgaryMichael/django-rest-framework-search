# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import six
import copy
import operator
import rest_framework.filters
import rest_framework.compat
from django.db.models import Q
from collections import OrderedDict
from .fields import SearchField


class SearchFilterMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs["_search_fields"] = cls._get_search_fields(bases, attrs)
        return super(SearchFilterMetaclass, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def _get_search_fields(cls, bases, attrs):
        fields = list()
        for field_name, obj in list(attrs.items()):
            if isinstance(obj, SearchField):
                neu = copy.deepcopy(obj)
                fields.append((field_name, neu))
                for alias in neu.aliases:
                    if alias not in list(name for name, _ in fields):
                        fields.append((alias, neu))

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


@six.add_metaclass(SearchFilterMetaclass)
class BaseSearchFilter(rest_framework.filters.SearchFilter):
    field_regex = r"\:([\w\s]+)\:(.*)"
    _defaults = None

    @property
    def default_fields(self):
        if self._defaults is None:
            self._defaults = OrderedDict(
                (field_name, field) for field_name, field
                in self._search_fields.items()
                if field.default is True)
        return self._defaults

    def filter_queryset(self, request, queryset, *args):
        try:
            searches = self.filter_searching(request)
        except AttributeError:
            return []  # return nothing on bad calls

        if len(searches) < 1:
            return queryset

        base = queryset
        queryset = queryset.filter(reduce(operator.or_, (Q(**search) for search in searches)))

        # Filtering against a many-to-many field requires us to
        # call queryset.distinct() in order to avoid duplicate items
        # in the resulting queryset.
        return rest_framework.compat.distinct(queryset, base)

    def construct_search(self, field):
        # in case this is every passed one of our fields
        if isinstance(field, fields.SearchField):
            return field.constructed
        return super(BaseSearchFilter, self).construct_search(six.string_types(field))

    def construct_field_name(self, field_name):
        return "_".join(field_name.split())

    def filter_searching(self, request):
        search_fields = set()
        for field_names, term in self.split_terms(request):
            for field in self._validate_fields(field_names, term):
                search_fields.add((field.constructed, term))
        return list(search_fields)

    def split_terms(self, request):
        split_terms = list()
        for search_term in self.get_search_terms(request):
            match = re.match(self.field_regex, search_term)
            if match:
                field = (self.construct_field_name(match.group(1)),)
                split_terms.append((field, match.group(2).strip()))
            else:
                field = tuple(self.default_fields.keys())
                split_terms.append((field, search_term.strip()))
        return split_terms

    def _validate_fields(self, field_names, search_term):
        valid_fields = set()
        for field_name in field_names:
            search_field = self._search_fields.get(field_name)
            if search_field is None:
                raise AttributeError("Field '{}' is not searchable".format(field_name))
            if search_field.is_valid(search_term):
                valid_fields.add(search_field)
        return valid_fields
