# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from collections import OrderedDict
from drf_search import filters, fields
from django.test import TestCase


class SearchFilterMetaclassTest(TestCase):
    def test_get_search_fields(self):
        attrs = [
            ("field1", fields.SearchField("pk", field_lookup="istartswith")),
            ("field2", fields.ExactSearchField("name", match_case=False, default=True)),
            ("field3", fields.ExactSearchField("something"))]
        search_fields = filters.SearchFilterMetaclass._get_search_fields((), dict(attrs))
        self.assertEqual(len(search_fields), 3)
        self.assertEqual(dict(search_fields), dict(attrs))

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

        expected_fields = OrderedDict([
            ("field2", test_fields["field2"]),
            ("field3", test_fields["field3"]),
            ("f3", test_fields["field3"]),
            ("field1", test_fields["field1"]),
            ("f1", test_fields["field1"])])
        self.assertEqual(search_fields, expected_fields)

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

        expected_fields = OrderedDict([
            ("fieldA", test_fields["fieldA"]),
            ("fieldB", test_fields["fieldB"]),
            ("fieldZ", test_fields["fieldZ"]),
            ("field2", test_fields["field2"]),
            ("field1", test_fields["field1"]),
            ("sharedfield", test_fields["sharedfield"])])
        self.assertEqual(search_fields, expected_fields)

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

        expected_fields = OrderedDict([
            ("fieldA", test_fields["fieldA"]),
            ("fa", test_fields["fieldA"]),
            ("fieldB", test_fields["fieldB"]),
            ("fb", test_fields["fieldB"]),
            ("fieldZ", test_fields["fieldZ"]),
            ("field2", test_fields["field2"]),
            ("field1", test_fields["field1"]),
            ("sharedfield", test_fields["sharedfield"]),
            ("s", test_fields["sharedfield"])])
        self.assertEqual(search_fields, expected_fields)

    def test_get_default_search_fields(self):
        attrs = [
            ("field1", fields.SearchField("pk", field_lookup="istartswith")),
            ("field2", fields.ExactSearchField("name", match_case=False, default=True)),
            ("field3", fields.ExactSearchField("something"))]
        search_fields = filters.SearchFilterMetaclass._get_default_search_fields(attrs)
        self.assertEqual(len(search_fields), 1)
        self.assertEqual(search_fields, [attrs[1]])
