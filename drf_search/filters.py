# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import six
import copy
import operator
import functools
import rest_framework.filters
import rest_framework.compat
from django.db.models import Q
from collections import OrderedDict, defaultdict
from rest_framework.exceptions import NotFound, ParseError
from .fields import SearchField


class SearchFilterMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        attrs["_search_fields"] = mcs._get_search_fields(bases, attrs)
        return super(SearchFilterMetaclass, mcs).__new__(mcs, name, bases, attrs)

    @classmethod
    def _get_search_fields(cls, bases, attrs):
        """Grabs a copy of all the `SearchField` classes that are associated with the class"""
        fields = list()
        for field_name, obj in attrs.items():
            if isinstance(obj, SearchField):
                neu = copy.deepcopy(obj)
                fields.append((field_name, neu))
                for alias in neu.aliases:
                    if alias not in list(name for name, _ in fields):
                        fields.append((alias, neu))

        # allow for subclassing
        # Note that we loop over the bases in *reversed*. This is necessary
        # in order to maintain the correct order of fields.
        for base in reversed(bases):
            base_fields = list()
            if hasattr(base, "_search_fields"):
                field_names = list(name for name, _ in fields)
                for field_name, obj in base._search_fields:
                    if field_name not in field_names:
                        base_fields.append((field_name, obj))
                    for alias in obj.aliases:
                        base_field_names = (name for name, _ in base_fields)
                        if alias not in field_names and alias not in list(base_field_names):
                            base_fields.append((alias, obj))
                fields = base_fields + fields
        return OrderedDict(fields)


@six.add_metaclass(SearchFilterMetaclass)
class BaseSearchFilter(rest_framework.filters.SearchFilter):
    field_regex = r"([\w]+\:)"

    @classmethod
    def get_field_names(cls):
        """Returns a list of all the field names for this class"""
        return list(six.text_type(name) for name, _ in cls._search_fields.items())

    @classmethod
    def get_default_fields(cls):
        """Returns all fields marked as default on the filter"""
        return OrderedDict(
            (six.text_type(field_name), field) for field_name, field
            in cls._search_fields.items()
            if field.default is True)

    def filter_queryset(self, request, queryset, *args):
        """Grabs all searches from the request and OR's each one into the same filter"""
        searches = self.filter_searching(request)

        if len(searches) < 1:
            if len(request.query_params.get(self.search_param, "")) > 0:
                raise ParseError("The search was not valid for any of the provided fields")
            return queryset  # we were not searching on anything

        base = queryset
        for term, fields in searches:
            queries = (Q(**{field: term}) for field in fields)
            queryset = queryset.filter(functools.reduce(operator.or_, queries))

        # Filtering against a many-to-many field requires us to
        # call queryset.distinct() in order to avoid duplicate items
        # in the resulting queryset.
        return rest_framework.compat.distinct(queryset, base)

    def construct_field_name(self, field_name):
        """
        Called on field names parsed from the search string.
        If the field name is erroneously typed (such as with excessive spaces),
        than this should be called to normalize the field name.
        This is useful as a way to have your field names more human readable.

        Example:
            input -> 'first name'
            output -> 'first_name'

        :param field_name: (str) the name of the field that was parsed from user input
        :return: (str) the repaired string
        """
        return "_".join(field_name.split())

    def filter_searching(self, request):
        """Returns a list of all valid constructed field name and search term associations"""
        searches = defaultdict(set)
        for field_names, term in self.split_terms(request):
            for field in self._validate_fields(field_names, term):
                searches[term].add(field.constructed)
        return list(searches.items())

    def get_search_terms(self, request):
        """Separates the search terms by commas"""
        params = request.query_params.get(self.search_param, "")
        return params.strip().split(",")

    def _iter_search(self, request):
        """Splits the raw search string into field and search term associations"""
        for search_term in self.get_search_terms(request):
            split_list = (split for split in re.split(self.field_regex, search_term.strip()) if split)
            while True:
                try:
                    split = next(split_list).strip()
                except StopIteration:
                    break
                field = None
                term = split
                if re.match(self.field_regex, split):
                    field = split.replace(":", "")
                    try:
                        term = next(split_list).strip() or None
                    except StopIteration:
                        term = None
                yield field, term

    def split_terms(self, request):
        """
        Constructs the field name + search term relationship that is yielded from `_iter_searching`.
        If no field is given by the search value, then this will default to using
        the list of default field names.

        Example:
            input -> ':jazz: first, second'
            output -> [(('jazz',), 'first'), (('default1', 'default2'), 'second')]

        :param request: The request object for the search
        :return: A list of tuples of field names (tuple of strings) and term (string) associations
        """
        split_terms = list()
        valid_field_names = self.get_field_names()
        for parsed_field, search_term in self._iter_search(request):
            if search_term is None:
                continue

            if parsed_field:
                field = self.construct_field_name(parsed_field)
                if field in valid_field_names:
                    split_terms.append(((field,), search_term))
                else:
                    default_fields = tuple(self.get_default_fields().keys())
                    split_terms.append((default_fields, "{}: {}".format(field, search_term)))
            else:
                field = tuple(self.get_default_fields().keys())
                split_terms.append((field, search_term))
        return split_terms

    def _validate_fields(self, field_names, search_term):
        """
        Converts the str names of the fields to the SearchField objects.
        Returns a set of all the associated fields that are passed that are valid
        for the search term.

        :param field_names (iterable): names/aliases of SearchFields for this filter
        :param search_term (str): search term that the fields will be searching for.
        :raises: AttributeError if a field name with no association is passed in
        :return (set): all the SearchFields passed in that are valid for the search term
        """
        for field_name in field_names:
            search_field = self._search_fields.get(field_name)
            if search_field is None:
                raise NotFound("Field '{}' is not searchable".format(field_name))
            if search_field.is_valid(search_term):
                yield search_field
