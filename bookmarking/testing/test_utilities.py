import unittest
import boto3
from moto import mock_s3
import datetime
import pytz
from bookmarking.utilities import get_bucket_prefix


class TestBucketPath(unittest.TestCase):

    def test_bucket_path_no_file(self):
        path = "s3://somebucket/someprefix/"
        expected_bucket = "somebucket"
        expected_prefix = "someprefix/"
        actual_bucket, actual_prefix = get_bucket_prefix(path)
        self.assertEqual(expected_bucket, actual_bucket)
        self.assertEqual(expected_prefix, actual_prefix)

