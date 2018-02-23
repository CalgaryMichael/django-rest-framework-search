# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from drf_search import validators


class ValidateNumerical(unittest.TestCase):
    def test_validate(self):
        self.assertTrue(validators.validate_numerical(123))
        self.assertTrue(validators.validate_numerical("123"))
        self.assertFalse(validators.validate_numerical("Jazz"))

        self.assertFalse(validators.validate_numerical([123]))
        self.assertFalse(validators.validate_numerical({123}))
        self.assertFalse(validators.validate_numerical((123,)))


class ValidateList(unittest.TestCase):
    def test_validate(self):
        self.assertTrue(validators.validate_list([1, 2, 3]))
        self.assertTrue(validators.validate_list("[1, 2, 3]"))

        self.assertFalse(validators.validate_list(123))
        self.assertFalse(validators.validate_list("jazz"))
        self.assertFalse(validators.validate_list({'a': 1, 'b': 2, 'c': 3}))
        self.assertFalse(validators.validate_list("{'a': 1, 'b': 2, 'c': 3}"))
