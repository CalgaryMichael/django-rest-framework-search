# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six
import mock
from contextlib import contextmanager
from drf_search import filters, fields
from django.test import TestCase
from rest_framework.exceptions import NotFound, ParseError


class TestFilter(filters.BaseSearchFilter):
    id = fields.IntegerSearchField("id", default=True)
    title = fields.SearchField("title", field_lookup="icontains")
    email = fields.SearchField("user__email", default=True, aliases="@",
                               validators=lambda x: not x.isdigit())
    contributor = fields.SearchField("contributors__display_name")


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

        expected_fields = ["fieldA", "fieldZ", "fieldB", "field2", "field1", "sharedfield"]
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

        expected_fields = ["fieldA", "fa", "fieldZ", "fieldB", "fb",
                           "field2", "field1", "sharedfield", "s"]
        self.assertEqual(list(search_fields.keys()), expected_fields)


class DefaultFieldsTests(BaseFilterTest):
    def test_simple(self):
        self.assertEqual(len(self.filterer.get_default_fields()), 3)

        default_keys = list(self.filterer.get_default_fields().keys())
        self.assertIn("id", default_keys)
        self.assertIn("email", default_keys)
        self.assertIn("@", default_keys)  # listens to aliases

    def test_no_reference(self):
        """After instantiation, no field that is changed will be listened to"""
        filter1 = TestFilter()
        filter2 = TestFilter()

        self.assertEqual(filter1.title.default, False)
        self.assertEqual(filter2.title.default, False)

        # both SearchField references are changed
        # because they both are referencing the same instantiated Search Field
        filter1.title.default = True
        self.assertEqual(filter1.title.default, True)
        self.assertEqual(filter2.title.default, True)

        # but the field that is saved by the Metaclass is not changed
        self.assertEqual(filter1._search_fields.get("title").default, False)
        self.assertEqual(filter2._search_fields.get("title").default, False)


class SplitTermsTests(BaseFilterTest):
    def setUp(self):
        super(SplitTermsTests, self).setUp()
        self.default_terms = ("email", "@", "id")

    def run_split_terms(self, *terms):
        with mock.patch("drf_search.filters.BaseSearchFilter._iter_search") as mock_iter:
            mock_iter.return_value = iter(terms)
            return self.filterer.split_terms(None)

    def test_default_terms(self):
        split_terms = self.run_split_terms((None, "Miles"), (None, "Davis"))
        self.assertEqual(split_terms, [(self.default_terms, "Miles"), (self.default_terms, "Davis")])

    def test_specified_fields(self):
        split_terms = self.run_split_terms(("contributor", "Miles"))
        self.assertEqual(split_terms, [(("contributor",), "Miles")])

    def test_mixed(self):
        split_terms = self.run_split_terms(("contributor", "Miles"), (None, "miles.davis@jazz.com"))
        self.assertEqual(split_terms, [(("contributor",), "Miles"), (self.default_terms, "miles.davis@jazz.com")])

        split_terms = self.run_split_terms(("contributor", None), ("email", "miles.davis@jazz.com"))
        self.assertEqual(split_terms, [(("email",), "miles.davis@jazz.com")])

        split_terms = self.run_split_terms(("contributor", None), (None, "miles.davis@jazz.com"))
        self.assertEqual(split_terms, [(self.default_terms, "miles.davis@jazz.com")])

    def test_no_data(self):
        split_terms = self.run_split_terms((None, None))
        self.assertEqual(split_terms, [])


class IterSearching(BaseFilterTest):
    def run_iter_searching(self, *terms):
        with mock_search_terms(*terms):
            return list(self.filterer._iter_search(None))

    def test_simple(self):
        result = self.run_iter_searching("title: draft")
        self.assertEqual(len(result), 1)
        self.assertEqual(result, [("title", "draft")])

    def test_comma_separation__specified(self):
        result = self.run_iter_searching("title: draft", "email: boris.badguy@example.com")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [("title", "draft"), ("email", "boris.badguy@example.com")])

    def test_comma_separation__mixed(self):
        result = self.run_iter_searching("draft", "email: boris.badguy@example.com")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [(None, "draft"), ("email", "boris.badguy@example.com")])

    def test_no_commas__specified(self):
        result = self.run_iter_searching("title: draft email: boris.badguy@example.com")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [("title", "draft"), ("email", "boris.badguy@example.com")])

    def test_no_commas__mixed(self):
        result = self.run_iter_searching("draft email: boris.badguy@example.com")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [(None, "draft"), ("email", "boris.badguy@example.com")])

    def test_no_term__first(self):
        result = self.run_iter_searching("title: email: boris.badguy@example.com")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [("title", None), ("email", "boris.badguy@example.com")])

    def test_no_term__last(self):
        result = self.run_iter_searching("title: draft email: ")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [("title", "draft"), ("email", None)])

    def test_no_term__both(self):
        result = self.run_iter_searching("title: email: ")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [("title", None), ("email", None)])


class ValidateFieldsTests(BaseFilterTest):
    def test_simple(self):
        search_fields = ("id", "title", "email")

        valid_fields = list(self.filterer._validate_fields(search_fields, "abcd"))
        self.assertEqual(len(valid_fields), 2)
        field_names = self._get_field_names(valid_fields)
        self.assertIn("user__email", field_names)
        self.assertIn("title", field_names)

        valid_fields = list(self.filterer._validate_fields(search_fields, "123"))
        self.assertEqual(len(valid_fields), 2)

        field_names = self._get_field_names(valid_fields)
        self.assertIn("id", field_names)
        self.assertIn("title", field_names)

    def test_aliases(self):
        search_fields = ("id", "@")
        valid_fields = list(self.filterer._validate_fields(search_fields, "abcd"))
        self.assertEqual(len(valid_fields), 1)
        self.assertEqual(self._get_field_names(valid_fields), ["user__email"])

    def test_aliases__multiple_references(self):
        """Returns all instance of valid SearchFields, including duplicates via aliases"""
        search_fields = ("id", "@", "email")
        valid_fields = list(self.filterer._validate_fields(search_fields, "miles.davis@jazz.com"))
        self.assertEqual(len(valid_fields), 2)
        self.assertEqual(self._get_field_names(valid_fields), ["user__email", "user__email"])

    def test_bad_field(self):
        with six.assertRaisesRegex(self, NotFound, "Field 'jazz' is not searchable"):
            list(self.filterer._validate_fields(("id", "@", "jazz"), "abcd"))


class FilterSearchingTests(BaseFilterTest):
    def test_simple(self):
        split_terms = [(("email", "title"), "Miles"), (("title",), "Davis")]
        result = self.run_filter_searching(*split_terms)
        self.assertEqual(len(result), 2)
        self.assertIn(("Miles", {"user__email__icontains", "title__icontains"}), result)
        self.assertIn(("Davis", {"title__icontains"}), result)

    def test_aliases(self):
        split_terms = [(("email", "@"), "Miles"), (("title",), "Davis")]
        result = self.run_filter_searching(*split_terms)
        self.assertEqual(len(result), 2)
        self.assertIn(("Miles", {"user__email__icontains"}), result)
        self.assertIn(("Davis", {"title__icontains"}), result)

    def test_bad_validation(self):
        split_terms = [(("id",), "Miles"), (("title",), "Davis")]
        result = self.run_filter_searching(*split_terms)
        self.assertEqual(len(result), 1)
        self.assertIn(("Davis", {"title__icontains"}), result)

    def test_error(self):
        split_terms = [(("id",), "Miles"), (("jazz",), "Davis")]
        with six.assertRaisesRegex(self, NotFound, "Field 'jazz' is not searchable"):
            self.run_filter_searching(*split_terms)
