import unittest
import boto3
from moto import mock_s3
from legacy.bookmarking.utilities import get_bucket_key, s3_key_exists

BUCKET = 'bucket1'


class TestBucketPath(unittest.TestCase):

    def test_bucket_path_no_file(self):
        path = "s3://somebucket/someprefix/"
        expected_bucket = "somebucket"
        expected_prefix = "someprefix/"
        actual_bucket, actual_prefix = get_bucket_key(path)
        self.assertEqual(expected_bucket, actual_bucket)
        self.assertEqual(expected_prefix, actual_prefix)


@mock_s3
class TestKeyExists(unittest.TestCase):

    def setUp(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        s3_client.create_bucket(
            ACL='private',
            Bucket=BUCKET
        )
        s3_client.upload_file('test_files/test_a.txt', BUCKET, 'uploaded.txt')


    def tearDown(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='uploaded.txt'
        )
        s3_client.delete_bucket(
            Bucket=BUCKET
        )

    def test_exists(self):
        s3 = boto3.client('s3')
        result = s3_key_exists(BUCKET, 'uploaded.txt', s3)
        self.assertTrue(result)

    def test_not_exists(self):
        s3 = boto3.client('s3')
        result = s3_key_exists(BUCKET, 'not_exist.txt', s3)
        self.assertFalse(result)
