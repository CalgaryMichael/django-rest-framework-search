# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .validators import validate_list, validate_numerical, validate_boolean, validate_email

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
    def __init__(self, field_name, field_lookup=None, validators=None,
                 default=False, match_case=None, aliases=None):
        self.field_name = field_name
        self.field_lookup = "icontains" if not match_case else "contains"
        if field_lookup is not None:
            # check to see if lookups are chained
            if all(lookup in VALID_LOOKUPS for lookup in field_lookup.split("__")):
                self.field_lookup = field_lookup
        self.match_case = match_case
        self.default = default
        self._constructed = None
        self._validators = []
        if validators is not None:
            self._validators = validators if isinstance(validators, list) else [validators]
        self.aliases = []
        if aliases is not None:
            self.aliases = aliases if isinstance(aliases, list) else [aliases]

    def __str__(self):
        return self.constructed

    def __deepcopy__(self, *args):
        return type(self)(
            self.field_name,
            field_lookup=self.field_lookup,
            default=self.default,
            match_case=self.match_case,
            validators=list(v for v in self._validators),
            aliases=list(a for a in self.aliases))

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
    def __init__(self, field_name, match_case=True, **kwargs):
        kwargs["field_lookup"] = "iexact"
        if match_case is True:
            kwargs["field_lookup"] = "exact"
        super(ExactSearchField, self).__init__(field_name, match_case=match_case, **kwargs)


class ContainsSearchField(SearchField):
    def __init__(self, field_name, match_case=False, **kwargs):
        kwargs["field_lookup"] = "icontains"
        if match_case is True:
            kwargs["field_lookup"] = "contains"
        super(ContainsSearchField, self).__init__(field_name, match_case=match_case, **kwargs)


class RegexSearchField(SearchField):
    def __init__(self, field_name, match_case=True, **kwargs):
        kwargs["field_lookup"] = "iregex"
        if match_case is True:
            kwargs["field_lookup"] = "regex"
        super(RegexSearchField, self).__init__(field_name, match_case=match_case, **kwargs)


class EmailSearchField(SearchField):
    def __init__(self, field_name, partial=False, match_case=False, **kwargs):
        kwargs["field_lookup"] = "icontains"
        if match_case is True:
            kwargs["field_lookup"] = "contains"
        super(EmailSearchField, self).__init__(field_name, match_case=match_case, **kwargs)
        if partial is False:
            self._validators = [validate_email] + self._validators


class IntegerSearchField(SearchField):
    def __init__(self, field_name, field_lookup="exact", **kwargs):
        super(IntegerSearchField, self).__init__(field_name, field_lookup=field_lookup, **kwargs)
        self._validators = [validate_numerical] + self._validators


class BooleanSearchField(SearchField):
    def __init__(self, field_name, field_lookup="iexact", **kwargs):
        super(BooleanSearchField, self).__init__(field_name, field_lookup=field_lookup, **kwargs)
        self._validators = [validate_boolean] + self._validators


class ListSearchField(SearchField):
    def __init__(self, field_name, **kwargs):
        kwargs["field_lookup"] = "in"
        super(ListSearchField, self).__init__(field_name, **kwargs)
        self._validators = [validate_list] + self._validators
