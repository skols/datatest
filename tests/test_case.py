# -*- coding: utf-8 -*-
import inspect
import re
from sys import version_info as _version_info
from unittest import TestCase as _TestCase  # Originial TestCase, not
                                            # compatibility layer.

# Import compatiblity layers.
from . import _io as io
from . import _unittest as unittest

# Import code to test.
from datatest.case import DataTestCase

from datatest.dataaccess import DataSource
from datatest.dataaccess import DataQuery
from datatest.dataaccess import DataResult

from datatest.errors import ValidationError
from datatest.errors import Extra
from datatest.errors import Missing
from datatest.errors import Invalid
from datatest.errors import Deviation

from datatest.allow import allow_error
from datatest.allow import allow_missing
from datatest.allow import allow_extra
from datatest.allow import allow_deviation
from datatest.allow import allow_percent_deviation
from datatest.allow import allow_limit
from datatest.allow import allow_specified


class TestHelperCase(unittest.TestCase):
    """Helper class for subsequent cases."""
    def _run_one_test(self, case, method):
        suite = unittest.TestSuite()
        audit_case = case(method)
        runner = unittest.TextTestRunner(stream=io.StringIO())
        test_result = runner.run(audit_case)
        self.assertEqual(test_result.testsRun, 1, 'Should one run test.')
        if test_result.errors:
            return test_result.errors[0][1]
        if test_result.failures:
            return test_result.failures[0][1]
        return None


class TestSubclass(TestHelperCase):
    def test_subclass(self):
        """DataTestCase should be a subclass of unittest.TestCase."""
        self.assertTrue(issubclass(DataTestCase, _TestCase))


class TestAssertValid(DataTestCase):
    """
    +------------------------------------------------------------+
    |      Object Comparisons and Returned *errors* Object       |
    +--------------+---------------------------------------------+
    |              |             *requirement* type              |
    | *data* type  +-------+---------+--------------+------------+
    |              | set   | mapping | sequence     | other      |
    +==============+=======+=========+==============+============+
    | **set**      | list  |         |              | list       |
    +--------------+-------+---------+--------------+------------+
    | **mapping**  | dict  | dict    | dict         | dict       |
    +--------------+-------+---------+--------------+------------+
    | **sequence** | list  |         | assert error | list       |
    +--------------+-------+---------+--------------+------------+
    | **iterable** | list  |         |              | list       |
    +--------------+-------+---------+--------------+------------+
    | **other**    | list  |         |              | data error |
    +--------------+-------+---------+--------------+------------+
    """
    def test_nonmapping(self):
        with self.assertRaises(ValidationError) as cm:
            data = set([1, 2, 3])
            required = set([1, 2, 4])
            self.assertValid(data, required)
        errors = cm.exception.errors

        self.assertEqual(errors, [Missing(4), Extra(3)])

    def test_data_mapping(self):
        with self.assertRaises(ValidationError) as cm:
            data = {'a': set([1, 2]), 'b': set([1]), 'c': set([1, 2, 3])}
            required = set([1, 2])
            self.assertValid(data, required)
        errors = cm.exception.errors

        self.assertEqual(errors, {'b': [Missing(2)], 'c': [Extra(3)]})

    def test_required_mapping(self):
        with self.assertRaises(ValidationError) as cm:
            data = {'AAA': 'a', 'BBB': 'x'}
            required = {'AAA': 'a', 'BBB': 'b', 'CCC': 'c'}
            self.assertValid(data, required)
        errors = cm.exception.errors

        self.assertEqual(errors, {'BBB': Invalid('x', 'b'), 'CCC': Missing('c')})

    def test_required_sequence(self):
        """When *required* is a sequence, _compare_sequence() should be
        called.
        """
        with self.assertRaises(AssertionError) as cm:
            data = ['a', 2, 'x', 3]
            required = ['a', 2, 'c', 4]
            self.assertValid(data, required)
        errors = cm.exception

        self.assertIsInstance(errors, AssertionError)

        error_string = str(errors)
        expected = 'Data sequence differs starting at index 2'
        self.assertTrue(error_string.startswith(expected))

    def test_required_other(self):
        """When *required* is a string or other object, _compare_other()
        should be called.
        """
        with self.assertRaises(ValidationError) as cm:
            required = lambda x: x.isupper()
            data = ['AAA', 'BBB', 'ccc', 'DDD']
            self.assertValid(data, required)
        errors = cm.exception.errors

        self.assertEqual = super(DataTestCase, self).assertEqual
        self.assertEqual(errors, [Invalid('ccc')])

    def test_query_objects(self):
        source = DataSource([('1', '2'), ('1', '2')], columns=['A', 'B'])
        query_obj1 = source(['B'])
        query_obj2 = source(['B'])
        self.assertValid(query_obj1, query_obj2)

    def test_result_objects(self):
        result_obj1 = DataResult(['2', '2'], evaluation_type=list)
        result_obj2 = DataResult(['2', '2'], evaluation_type=list)
        self.assertValid(result_obj1, result_obj2)


class TestAssertEqual(unittest.TestCase):
    def test_for_unwrapped_behavior(self):
        """The datatest.DataTestCase class should NOT wrap the
        assertEqual() method of its superclass. In version 0.7.0,
        datatest DID wrap this method--this test should remain part
        of the suite to prevent regression.
        """
        with self.assertRaises(Exception) as cm:
            first  = set([1,2,3,4,5,6,7])
            second = set([1,2,3,4,5,6])
            self.assertEqual(first, second)

        self.assertIs(type(cm.exception), AssertionError)


class TestAllowanceWrappers(unittest.TestCase):
    """Test method wrappers for allowance context managers."""
    def setUp(self):
        class DummyCase(DataTestCase):
            def runTest(self):
                pass
        self.case = DummyCase()

    def test_allowSpecified(self):
        cm = self.case.allowSpecified([Missing('foo')])
        self.assertTrue(isinstance(cm, allow_specified))

    def test_allowAll(self):
        cm = self.case.allowAll(lambda x: x == 'aaa')
        self.assertTrue(isinstance(cm, allow_error))

    def test_allowMissing(self):
        cm = self.case.allowMissing()
        self.assertTrue(isinstance(cm, allow_missing))

    def test_allowExtra(self):
        cm = self.case.allowExtra()
        self.assertTrue(isinstance(cm, allow_extra))

    def test_allowDeviation(self):
        cm = self.case.allowDeviation(5)
        self.assertTrue(isinstance(cm, allow_deviation))

    def test_allowPercentDeviation(self):
        result = self.case.allowPercentDeviation(5)
        self.assertTrue(isinstance(result, allow_percent_deviation))

    def test_allowLimit(self):
        cm = self.case.allowLimit(10)
        self.assertTrue(isinstance(cm, allow_limit))
