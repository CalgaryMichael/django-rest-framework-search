# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six
import mock
from contextlib import contextmanager
from collections import OrderedDict
from drf_search import filters, fields
from django.test import TestCase


class TestFilter(filters.BaseSearchFilter):
    id = fields.IntegerSearchField("id", default=True)
    title = fields.SearchField("title", field_lookup="icontains")
    email = fields.SearchField("user__email", default=True, aliases="@",
                               validators=lambda x: not x.isdigit())


@contextmanager
def mock_search_terms(*terms):
    with mock.patch("drf_search.filters.BaseSearchFilter.get_search_terms") as mock_terms:
        mock_terms.return_value = list(terms)
        yield


class BaseFilterTest(TestCase):
    def setUp(self):
        self.filterer = TestFilter()

    def _get_field_names(self, fields):
        return list(field.field_name for field in fields)

    def run_filter_searching(self, *terms):
        with mock_search_terms(*terms):
            return self.filterer.filter_searching(None)

    def run_filter_queryset(self, *terms):
        queryset = None  # TODO figure out how to do this. Prop up a db, I guess?
        with mock_search_terms(*terms):
            return self.filterer.filter_queryset(None, queryset)

    def run_filter_searching(self, *args):
        with mock.patch("drf_search.filters.BaseSearchFilter.split_terms") as mock_split:
            mock_split.return_value = list(args)
            return self.filterer.filter_searching(None)


class SearchFilterMetaclassTest(TestCase):
    def test_get_search_fields(self):
        attrs = [
            ("field1", fields.SearchField("pk", field_lookup="istartswith")),
            ("field2", fields.ExactSearchField("name", match_case=False, default=True)),
            ("field3", fields.ExactSearchField("something"))]
        search_fields = filters.SearchFilterMetaclass._get_search_fields((), dict(attrs))
        self.assertEqual(len(search_fields), 3)
        expected_fields = ["field2", "field3", "field1"]
        self.assertEqual(list(search_fields.keys()), expected_fields)

    def test_get_search_fields__with_aliases(self):
        test_fields = {
            "field1": fields.SearchField("pk", field_lookup="istartswith", aliases="f1"),
            "field2": fields.ExactSearchField("name", match_case=False, default=True),
            "field3": fields.ExactSearchField("something", aliases=["f3"])}

        attrs = [
            ("field1", test_fields["field1"]),
            ("field2", test_fields["field2"]),
            ("field3", test_fields["field3"])]
        search_fields = filters.SearchFilterMetaclass._get_search_fields((), dict(attrs))
        self.assertEqual(len(search_fields), 5)

        expected_fields = ["field2", "field3", "f3", "field1", "f1"]
        self.assertEqual(list(search_fields.keys()), expected_fields)

    def test_get_search_fields__with_bases(self):
        test_fields = {
            "fieldA": fields.IntegerSearchField("id"),
            "fieldB": fields.RegexSearchField("title"),
            "fieldZ": fields.BooleanSearchField("active"),
            "field1": fields.SearchField("pk", field_lookup="istartswith"),
            "field2": fields.ExactSearchField("name", match_case=False, default=True),
            "sharedfield": fields.ExactSearchField("something")}

        class Example(object):
            _search_fields = [
                ("fieldA", test_fields["fieldA"]),
                ("fieldB", test_fields["fieldB"]),
                ("sharedfield", test_fields["sharedfield"])]

        class Example2(object):
            _search_fields = [
                ("fieldZ", test_fields["fieldZ"]),
                ("fieldB", test_fields["fieldB"]),
                ("sharedfield", test_fields["sharedfield"])]

        bases = (Example, Example2)
        attrs = [
            ("field1", test_fields["field1"]),
            ("field2", test_fields["field2"]),
            ("sharedfield", test_fields["sharedfield"])]
        search_fields = filters.SearchFilterMetaclass._get_search_fields(bases, dict(attrs))
        self.assertEqual(len(search_fields), 6)

        expected_fields = ["fieldA", "fieldB", "fieldZ", "field2", "field1", "sharedfield"]
        self.assertEqual(list(search_fields.keys()), expected_fields)

    def test_get_search_fields__with_bases__with_aliases(self):
        test_fields = {
            "fieldA": fields.IntegerSearchField("id", aliases="fa"),
            "fieldB": fields.RegexSearchField("title", aliases="fb"),
            "fieldZ": fields.BooleanSearchField("active"),
            "field1": fields.SearchField("pk", field_lookup="istartswith"),
            "field2": fields.ExactSearchField("name", match_case=False, default=True),
            "sharedfield": fields.ExactSearchField("something", aliases=["s"])}

        class Example(object):
            _search_fields = [
                ("fieldA", test_fields["fieldA"]),
                ("fieldB", test_fields["fieldB"]),
                ("sharedfield", test_fields["sharedfield"])]

        class Example2(object):
            _search_fields = [
                ("fieldZ", test_fields["fieldZ"]),
                ("fieldB", test_fields["fieldB"]),
                ("sharedfield", test_fields["sharedfield"])]

        bases = (Example, Example2)
        attrs = [
            ("field1", test_fields["field1"]),
            ("field2", test_fields["field2"]),
            ("sharedfield", test_fields["sharedfield"])]
        search_fields = filters.SearchFilterMetaclass._get_search_fields(bases, dict(attrs))
        self.assertEqual(len(search_fields), 9)

        expected_fields = ["fieldA", "fa", "fieldB", "fb",
                           "fieldZ", "field2", "field1", "sharedfield", "s"]
        self.assertEqual(list(search_fields.keys()), expected_fields)


class DefaultFieldsTests(BaseFilterTest):
    def setUp(self):
        self.filterer = TestFilter()

    def test_cache(self):
        self.assertEqual(self.filterer._defaults, None)
        self.assertEqual(len(self.filterer.default_fields), 3)
        self.assertEqual(len(self.filterer._defaults), 3)

    def test_simple(self):
        self.assertEqual(len(self.filterer.default_fields), 3)

        default_keys = list(self.filterer.default_fields.keys())
        self.assertIn("id", default_keys)
        self.assertIn("email", default_keys)
        self.assertIn("@", default_keys)  # listens to aliases

    def test_no_reference(self):
        """After instatiation, no field that is changed will be listened to"""
        filter1 = TestFilter()
        filter2 = TestFilter()

        self.assertEqual(filter1.title.default, False)
        self.assertEqual(filter2.title.default, False)

        # both SearchField references are changed
        # because they both are referencing the same instatiated Search Field
        filter1.title.default = True
        self.assertEqual(filter1.title.default, True)
        self.assertEqual(filter2.title.default, True)

        # but the field that is saved by the Metaclass is not changed
        self.assertEqual(filter1._search_fields.get("title").default, False)
        self.assertEqual(filter2._search_fields.get("title").default, False)


class SplitTermsTests(BaseFilterTest):
    def test_split_terms(self):
        # no speicified field results in default search field
        default_terms = ("email", "@", "id")
        with mock_search_terms("Miles", "Davis"):
            split_terms = self.filterer.split_terms(None)
        self.assertEqual(split_terms, [(default_terms, "Miles"), (default_terms, "Davis")])

        # grabs the specified field
        with mock_search_terms(":contributor:Miles"):
            split_terms = self.filterer.split_terms(None)
        self.assertEqual(split_terms, [(("contributor",), "Miles")])

        # mixed
        with mock_search_terms(":contributor:Miles", "miles.davis@jazz.com"):
            split_terms = self.filterer.split_terms(None)
        self.assertEqual(split_terms, [(("contributor",), "Miles"), (default_terms, "miles.davis@jazz.com")])

        # edge case
        with mock_search_terms(":first  name:   Miles   "):
            split_terms = self.filterer.split_terms(None)
        self.assertEqual(split_terms, [(("first_name",), "Miles")])


class ValidateFieldsTests(BaseFilterTest):
    def test_simple(self):
        search_fields = ("id", "title", "email")

        valid_fields = self.filterer._validate_fields(search_fields, "abcd")
        self.assertEqual(len(valid_fields), 2)
        field_names = self._get_field_names(valid_fields)
        self.assertIn("user__email", field_names)
        self.assertIn("title", field_names)

        valid_fields = self.filterer._validate_fields(search_fields, "123")
        self.assertEqual(len(valid_fields), 2)

        field_names = self._get_field_names(valid_fields)
        self.assertIn("id", field_names)
        self.assertIn("title", field_names)

    def test_aliases(self):
        search_fields = ("id", "@")
        valid_fields = self.filterer._validate_fields(search_fields, "abcd")
        self.assertEqual(len(valid_fields), 1)
        self.assertEqual(self._get_field_names(valid_fields), ["user__email"])

    def test_aliases__multiple_references(self):
        """Only returns one SearchField instance with two aliases"""
        search_fields = ("id", "@", "email")
        valid_fields = self.filterer._validate_fields(search_fields, "miles.davis@jazz.com")
        self.assertEqual(len(valid_fields), 1)
        self.assertEqual(self._get_field_names(valid_fields), ["user__email"])

    def test_bad_field(self):
        with six.assertRaisesRegex(self, AttributeError, "Field 'jazz' is not searchable"):
            self.filterer._validate_fields(("id", "@", "jazz"), "abcd")


class FilterSearchingTests(BaseFilterTest):
    def test_simple(self):
        split_terms = [(("email",), "Miles"), (("title",), "Davis")]
        result = self.run_filter_searching(*split_terms)
        self.assertEqual(len(result), 2)
        self.assertIn(("user__email__icontains", "Miles"), result)
        self.assertIn(("title__icontains", "Davis"), result)

    def test_aliases(self):
        split_terms = [(("email", "@"), "Miles"), (("title",), "Davis")]
        result = self.run_filter_searching(*split_terms)
        self.assertEqual(len(result), 2)
        self.assertIn(("user__email__icontains", "Miles"), result)
        self.assertIn(("title__icontains", "Davis"), result)

    def test_bad_validation(self):
        split_terms = [(("id",), "Miles"), (("title",), "Davis")]
        result = self.run_filter_searching(*split_terms)
        self.assertEqual(len(result), 1)
        self.assertIn(("title__icontains", "Davis"), result)

    def test_error(self):
        split_terms = [(("id",), "Miles"), (("jazz",), "Davis")]
        with six.assertRaisesRegex(self, AttributeError, "Field 'jazz' is not searchable"):
            self.run_filter_searching(*split_terms)
