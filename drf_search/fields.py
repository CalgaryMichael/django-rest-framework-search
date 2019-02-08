# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import six
import inspect
from .validators import validate_list, validate_numerical, validate_boolean, validate_email, validate_string

# Ref: https://docs.djangoproject.com/en/2.0/ref/models/querysets/#field-lookups
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
    """
    The base SearchField that handles the logic of representing and validating a field.

    :attr field_name (str): The name of the model's field (ex: `title`)
    :attr field_lookup (str): The name of the desired lookup (ex: `icontains`)
    :attr validators (list): Pre-search validators that should determine whether the input is valid for the field
    :attr default (bool): Determines whether this field should be used if no fields are specified during search
    :attr match_case (bool): Determines whether to use the case sensitive field lookup
    :attr aliases (list): Alternative names that can be used to refer to the SearchField
    """

    def __init__(self, field_name, field_lookup=None, validators=None,
                 default=False, match_case=None, aliases=None, **kwargs):
        self.field_name = field_name
        self.field_lookup = "contains" if match_case else "icontains"
        if field_lookup is not None:
            # check to see if lookups are chained
            if all(lookup in VALID_LOOKUPS for lookup in field_lookup.split("__")):
                self.field_lookup = field_lookup
        self.match_case = match_case
        self.default = default
        self._constructed = None
        self._validators = []
        if validators is not None:
            self._validators = [validators] if inspect.isfunction(validators) else list(validators)
        self.aliases = []
        if aliases is not None:
            self.aliases = [aliases] if isinstance(aliases, six.string_types) else list(aliases)

    def __str__(self):
        return self.constructed

    def __deepcopy__(self, *args):
        partial = getattr(self, "partial", None)  # needed for EmailSearchField
        return type(self)(
            self.field_name,
            field_lookup=self.field_lookup,
            default=self.default,
            match_case=self.match_case,
            partial=partial,
            validators=list(v for v in self._validators),
            aliases=list(a for a in self.aliases))

    @property
    def constructed(self):
        """Constructs the django ORM query field lookup."""
        if self._constructed is None:
            field_lookup = ""
            if self.field_lookup:
                field_lookup = "__{}".format(self.field_lookup)
            self._constructed = "{field}{lookup}".format(field=self.field_name, lookup=field_lookup)
        return self._constructed

    def is_valid(self, search_value):
        """Determines whether the `search_value` passes every validators for this field"""
        return all(validator(search_value) for validator in self._validators)


class ExactSearchField(SearchField):
    """SearchField for searching by `exact` or `iexact`"""
    def __init__(self, field_name, match_case=True, **kwargs):
        kwargs["field_lookup"] = "exact" if match_case else "iexact"
        super(ExactSearchField, self).__init__(field_name, match_case=match_case, **kwargs)


class StringSearchField(SearchField):
    """SearchField that validates the search value as a strictly non-numerical string"""
    def __init__(self, field_name, **kwargs):
        super(StringSearchField, self).__init__(field_name, **kwargs)
        self._validators = [validate_string] + self._validators


class RegexSearchField(SearchField):
    """SearchField for searching by `regex` or `iregex`"""
    def __init__(self, field_name, match_case=True, **kwargs):
        kwargs["field_lookup"] = "regex" if match_case else "iregex"
        super(RegexSearchField, self).__init__(field_name, match_case=match_case, **kwargs)


class EmailSearchField(SearchField):
    """
    SearchField for searching by `contains` or `icontains`

    :attr partial (bool): Determines whether to allow searching by partial or full emails
                          If False, a validator that matches the search value as an email will be added
    """
    def __init__(self, field_name, partial=False, match_case=False, **kwargs):
        if partial is False:
            kwargs["field_lookup"] = "exact" if match_case else "iexact"
        else:
            kwargs["field_lookup"] = "contains" if match_case else "icontains"
        super(EmailSearchField, self).__init__(field_name, match_case=match_case, **kwargs)
        self.partial = partial
        self._validators.append(lambda x: not re.search(r"\s", x.strip()))
        if self.partial is False:
            self._validators = [validate_email] + self._validators


class IntegerSearchField(SearchField):
    """SearchField that validates the search value as a strictly numerical value"""
    def __init__(self, field_name, field_lookup="exact", **kwargs):
        super(IntegerSearchField, self).__init__(field_name, field_lookup=field_lookup, **kwargs)
        self._validators = [validate_numerical] + self._validators


class BooleanSearchField(SearchField):
    """
    SearchField that validates the search value as a boolean value
    The following will be valid, as well as their case-insensitive equivalent:
        `True`, `False`, `1`, `0`
    """
    def __init__(self, field_name, field_lookup="iexact", **kwargs):
        super(BooleanSearchField, self).__init__(field_name, field_lookup=field_lookup, **kwargs)
        self._validators = [validate_boolean] + self._validators


class ListSearchField(SearchField):
    """SearchField that expects a list as the search value"""
    def __init__(self, field_name, **kwargs):
        kwargs["field_lookup"] = "in"
        super(ListSearchField, self).__init__(field_name, **kwargs)
        self._validators = [validate_list] + self._validators
