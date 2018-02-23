# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from mock import patch
from drf_search import fields, validators


class SearchFieldTest(unittest.TestCase):
    def test_base(self):
        """base test, no extra frills"""
        field = fields.SearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.field_lookup, "icontains")
        self.assertEqual(field.constructed, "pk__icontains")
        self.assertEqual(field.default, False)
        self.assertEqual(field._validators, [])

        field = fields.SearchField(
            "pk",
            field_lookup="exact",
            default=True,
            validators=validators.validate_list)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.field_lookup, "exact")
        self.assertEqual(field.constructed, "pk__exact")
        self.assertEqual(field.default, True)
        self.assertEqual(field._validators, [validators.validate_list])

    def test_validators(self):
        # no validators
        field = fields.SearchField("pk")
        self.assertTrue(isinstance(field._validators, list))
        self.assertEqual(len(field._validators), 0)
        self.assertTrue(field.is_valid("this will always pass"))

        # if a validator returns a bad result
        field = fields.SearchField("pk", validators=[lambda x: True, lambda x: False])
        self.assertTrue(isinstance(field._validators, list))
        self.assertEqual(len(field._validators), 2)
        self.assertFalse(field.is_valid("this will always fail"))

        # a test with a real validator
        field = fields.SearchField("pk", validators=validators.validate_numerical)
        self.assertTrue(isinstance(field._validators, list))
        self.assertEqual(len(field._validators), 1)
        self.assertTrue(field.is_valid("9780123456789"))
        self.assertFalse(field.is_valid("abcdef"))

    def test_field_lookup(self):
        field = fields.SearchField("pk")
        self.assertEqual(field.field_lookup, "icontains")

        field = fields.SearchField("pk", field_lookup="regex")
        self.assertEqual(field.field_lookup, "regex")

        field = fields.SearchField("pk", field_lookup="jazz")
        self.assertEqual(field.field_lookup, "icontains")

    def test_field_lookup__chained(self):
        field = fields.SearchField("pk", field_lookup="month__gte")
        self.assertEqual(field.field_lookup, "month__gte")

        field = fields.SearchField("pk", field_lookup="jazz__gte")
        self.assertEqual(field.field_lookup, "icontains")

        field = fields.SearchField("pk", field_lookup="hour__jazz")
        self.assertEqual(field.field_lookup, "icontains")

    def test_constructed(self):
        field = fields.SearchField("pk")
        expected_constructed = "pk__icontains"
        self.assertEqual(field._constructed, None)
        self.assertEqual(field.constructed, expected_constructed)
        self.assertEqual(field._constructed, expected_constructed)

        # test if no field_lookup
        field = fields.SearchField("pk")
        expected_constructed = "pk"
        self.assertEqual(field._constructed, None)
        with patch.object(field, "field_lookup", new=None):
            self.assertEqual(field.constructed, expected_constructed)
        self.assertEqual(field._constructed, expected_constructed)

        # test if empty field lookup
        field = fields.SearchField("pk")
        expected_constructed = "pk"
        self.assertEqual(field._constructed, None)
        with patch.object(field, "field_lookup", new=""):
            self.assertEqual(field.constructed, expected_constructed)
        self.assertEqual(field._constructed, expected_constructed)


class ExactSearchFieldTests(unittest.TestCase):
    def test_simple(self):
        # basic, no frills
        field = fields.ExactSearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, True)
        self.assertEqual(field.field_lookup, "exact")

        # changes with match_case
        field = fields.ExactSearchField("pk", match_case=False)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, False)
        self.assertEqual(field.field_lookup, "iexact")

    def test_field_lookup(self):
        field = fields.ExactSearchField("pk", field_lookup="contains")
        self.assertEqual(field.match_case, True)
        self.assertEqual(field.field_lookup, "exact")

        field = fields.ExactSearchField("pk", field_lookup="contains", match_case=False)
        self.assertEqual(field.match_case, False)
        self.assertEqual(field.field_lookup, "iexact")


class ContainsSearchFieldTests(unittest.TestCase):
    def test_simple(self):
        # basic, no frills
        field = fields.ContainsSearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, False)
        self.assertEqual(field.field_lookup, "icontains")

        # changes with match_case
        field = fields.ContainsSearchField("pk", match_case=True)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, True)
        self.assertEqual(field.field_lookup, "contains")

    def test_field_lookup(self):
        field = fields.ContainsSearchField("pk", field_lookup="exact")
        self.assertEqual(field.match_case, False)
        self.assertEqual(field.field_lookup, "icontains")

        field = fields.ContainsSearchField("pk", field_lookup="exact", match_case=True)
        self.assertEqual(field.match_case, True)
        self.assertEqual(field.field_lookup, "contains")


class RegexSearchFieldTests(unittest.TestCase):
    def test_simple(self):
        # basic, no frills
        field = fields.RegexSearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, True)
        self.assertEqual(field.field_lookup, "regex")

        # changes with match_case
        field = fields.RegexSearchField("pk", match_case=False)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, False)
        self.assertEqual(field.field_lookup, "iregex")

    def test_field_lookup(self):
        field = fields.RegexSearchField("pk", field_lookup="exact")
        self.assertEqual(field.match_case, True)
        self.assertEqual(field.field_lookup, "regex")

        field = fields.RegexSearchField("pk", field_lookup="exact", match_case=False)
        self.assertEqual(field.match_case, False)
        self.assertEqual(field.field_lookup, "iregex")


class IntegerSearchFieldTests(unittest.TestCase):
    def test_simple(self):
        field = fields.IntegerSearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, None)
        self.assertEqual(field.field_lookup, "exact")
        self.assertEqual(len(field._validators), 1)

        field = fields.IntegerSearchField(
            "pk",
            field_lookup="contains",
            validators=lambda x: len(x) == 13)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, None)
        self.assertEqual(field.field_lookup, "contains")
        self.assertEqual(len(field._validators), 2)

    def test_is_valid(self):
        field = fields.IntegerSearchField("pk")
        self.assertTrue(field.is_valid("123"))
        self.assertFalse(field.is_valid("abc"))

        field = fields.IntegerSearchField("pk", validators=lambda x: len(x) == 13)
        self.assertFalse(field.is_valid("123"))
        self.assertTrue(field.is_valid("9780123456789"))


class BooleanSearchFieldTests(unittest.TestCase):
    def test_simple(self):
        field = fields.BooleanSearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, None)
        self.assertEqual(field.field_lookup, "iexact")
        self.assertEqual(len(field._validators), 1)

        field = fields.BooleanSearchField(
            "pk",
            field_lookup="contains",
            validators=lambda x: len(x) == 13)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, None)
        self.assertEqual(field.field_lookup, "contains")
        self.assertEqual(len(field._validators), 2)

    def test_is_valid(self):
        field = fields.BooleanSearchField("pk")
        self.assertTrue(field.is_valid(True))
        self.assertTrue(field.is_valid("True"))
        self.assertTrue(field.is_valid(False))
        self.assertTrue(field.is_valid("False"))
        self.assertFalse(field.is_valid("abc"))

        field = fields.BooleanSearchField("pk", validators=lambda x: x == False)
        self.assertFalse(field.is_valid(True))
        self.assertFalse(field.is_valid("True"))
        self.assertTrue(field.is_valid(False))
        self.assertFalse(field.is_valid("False"))
        self.assertFalse(field.is_valid("abc"))


class ListSearchFieldTests(unittest.TestCase):
    def test_simple(self):
        field = fields.ListSearchField("pk")
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, None)
        self.assertEqual(field.field_lookup, "in")
        self.assertEqual(len(field._validators), 1)

        field = fields.ListSearchField(
            "pk",
            field_lookup="contains",
            validators=lambda x: len(x) == 3)
        self.assertEqual(field.field_name, "pk")
        self.assertEqual(field.match_case, None)
        self.assertEqual(field.field_lookup, "in")
        self.assertEqual(len(field._validators), 2)

    def test_is_valid(self):
        field = fields.ListSearchField("pk")
        self.assertTrue(field.is_valid([123, "abc"]))
        self.assertFalse(field.is_valid("abc"))

        field = fields.ListSearchField("pk", validators=lambda x: len(x) == 3)
        self.assertFalse(field.is_valid([123, "abc"]))
        self.assertTrue(field.is_valid([1, 2, 3]))
