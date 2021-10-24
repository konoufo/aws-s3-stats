import json
import sys
import unittest
from unittest.mock import MagicMock, patch

import controller
from s3cli import S3Cli


class FakeConsole:
    def __init__(self):
        self._buffer = ''

    def write(self, s):
        self._buffer += s

    def read(self):
        return self._buffer

    def clear(self):
        self = FakeConsole()


class CLITestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._sys_stdout = sys.stdout
        self.console = FakeConsole()
        sys.stdout = self.console

        s3_controller = MagicMock()
        s3_controller.configure_mock(
            list_buckets=MagicMock(return_value=[MagicMock()]),
            get_region=MagicMock(return_value='us-east-1'),
            get_bucket_info=MagicMock(return_value=controller.BucketInfo(name='foobar'))
        )
        
        self.cli = S3Cli(s3_controller=s3_controller)

    def tearDown(self):
        print(self.console.read())
        sys.stdout = self._sys_stdout
        self.console.clear()
        return super().tearDown()
    
    @patch('sys.argv', [])
    def test_display_all(self):
       self.cli.run()

       assert self.console.read() != ''


class ControllerTestCase(unittest.TestCase):
    with open('pricing.json') as f:
        prices = json.load(f)

    def setUp(self):
        super().setUp()
        self.s3_resource = MagicMock()
        self.s3_resource.configure_mock(
            buckets=MagicMock(filter=MagicMock())
        )
        self.controller = controller.S3(s3_resource=self.s3_resource)

    
    def test_compute_price(self):
        for storage_class, expected_price in self.prices.items():
            assert controller.Pricing.compute_gigabyte_price(storage_class) == expected_price
    
    def test_list_buckets(self):
        filters = {'filtre1': 'foo', 'filtre2': 'bar'}
        self.controller.list_buckets(**filters)

        self.s3_resource.buckets.filter.assert_called_with(**filters)
