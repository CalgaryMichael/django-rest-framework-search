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
