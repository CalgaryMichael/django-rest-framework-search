# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .validators import validate_list, validate_numerical

VALID_LOOKUPS = [
    "exact", "iexact",
    "contains", "icontains",
    "startswith", "istartswith",
    "endswith", "iendswith",
    "regex", "iregex",
    "gt", "gte",
    "lt", "lte",
    "in", "isnull",
    "range", "date",
    "year", "month", "week", "week_day", "quarter",
    "time", "hour", "minute", "second"]


class SearchField(object):
    def __init__(self, field_name, field_lookup=None, validators=None, default=False):
        self.field_name = field_name
        self.field_lookup = "icontains"
        if field_lookup is not None:
            # check to see if lookups are chained
            if all(lookup in VALID_LOOKUPS for lookup in field_lookup.split("__")):
                self.field_lookup = field_lookup
        self.default = default
        self._constructed = None
        self._validators = []
        if validators is not None:
            self._validators = validators if isinstance(validators, list) else [validators]

    def __str__(self):
        return self.constructed

    @property
    def constructed(self):
        if self._constructed is None:
            field_lookup = ""
            if self.field_lookup:
                field_lookup = "__{}".format(self.field_lookup)
            self._constructed = "{field}{lookup}".format(field=self.field_name, lookup=field_lookup)
        return self._constructed

    def is_valid(self, search_value):
        return all(validator(search_value) for validator in self._validators)


class ExactSearchField(SearchField):
    def __init__(self, match_case=True, *args, **kwargs):
        kwargs["field_lookup"] = "iexact"
        if match_case is True:
            kwargs["field_lookup"] = "exact"
        super(ExactSearchField, self).__init__(field_lookup=field_lookup, *args, **kwargs)


class ContainsSearchField(SearchField):
    def __init__(self, match_case=False, *args, **kwargs):
        kwargs["field_lookup"] = "icontains"
        if match_case is True:
            kwargs["field_lookup"] = "contains"
        super(ContainsSearchField, self).__init__(field_lookup=field_lookup, *args, **kwargs)


class RegexSearchField(SearchField):
    def __init__(self, match_case=True, *args, **kwargs):
        kwargs["field_lookup"] = "iregex"
        if match_case is True:
            kwargs["field_lookup"] = "regex"
        super(RegexSearchField, self).__init__(field_lookup=field_lookup, *args, **kwargs)


class IntegerSearchField(SearchField):
    def __init__(self, field_lookup="exact", *args, **kwargs):
        super(IntegerSearchField, self).__init__(field_lookup=field_lookup, *args, **kwargs)
        self._validators = [validate_numerical] + self._validators


class ListSearchField(SearchField):
    def __init__(self, *args, **kwargs):
        super(ListSearchField, self).__init__(field_lookup="in", *args, **kwargs)
        self._validators = [validate_list] + self._validators
