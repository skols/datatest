
import pytest
from datatest import working_directory
from datatest import Selector
from datatest import DataTestCase
from datatest import mandatory
from datatest import Missing, Extra, Deviation, Invalid


# Define fixtures.

def setUpModule():
    global detail
    global summary

    with working_directory(__file__):
        detail = Selector('country_of_birth.csv')
        summary = Selector('estimated_totals.csv')


# Begin tests.

class TestPopulation(DataTestCase):

    @mandatory
    def test_columns(self):
        required_set = set(summary.fieldnames)

        self.assertValid(detail.fieldnames, required_set)

    def test_state_labels(self):
        data = detail({'state/territory'})
        requirement = summary({'state/territory'})

        self.assertValid(data, requirement)

    def test_population_format(self):
        data = detail({'population'})

        def integer_format(x):  # <- Helper function.
            return str(x).isdecimal()

        self.assertValid(data, integer_format)

    def test_population_sums(self):
        data = detail({'state/territory': 'population'}).sum()
        requirement = summary({'state/territory': 'population'}).sum()

        self.assertValid(data, requirement)
