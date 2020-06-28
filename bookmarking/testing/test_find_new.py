import unittest
import boto3
from moto import mock_s3
import datetime
import pytz
from bookmarking.find_new_files import remove_common


class TestRemoveCommon(unittest.TestCase):
        def test_remove_common(self):
            needs_removal = [1, 2, 3, 4, 5, 6]
            to_remove = [2, 4, 5]
            result = remove_common(needs_removal, to_remove)
            expected_result = [1, 3, 6]
            self.assertCountEqual(result, expected_result)


# @mock_s3
# class TestFindLatest(unittest.TestCase):
#     start_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
#