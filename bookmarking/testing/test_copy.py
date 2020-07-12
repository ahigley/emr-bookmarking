import unittest
import boto3
from moto import mock_s3
from bookmarking.s3_copy import copy_prefix_threaded
from bookmarking.utilities import get_bucket_key

BUCKET = 'mock-test-bucket'
BUCKET2 = 'copy-to-bucket'
local_files = ['test_files/test_a.txt', 'test_files/test_b.txt']


@mock_s3
class TestListS3FilesFull(unittest.TestCase):

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
        s3_client.create_bucket(
            ACL='private',
            Bucket=BUCKET2
        )
        for x in range(0, 1000):
            s3_client.upload_file(local_files[0], BUCKET, local_files[0].replace('a', str(x)))
            s3_client.upload_file(local_files[0], BUCKET,
                                  F"subprefix1/subprefix2/{local_files[1].replace('b', str(x))}")
        for x in range(1000, 2000):
            s3_client.upload_file(local_files[0], BUCKET, local_files[0].replace('a', str(x)))
            s3_client.upload_file(local_files[0], BUCKET,
                                  F"subprefix1/subprefix2/subprefix3/{local_files[1].replace('b', str(x))}")

    def tearDown(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        for x in range(0, 1000):
            s3_client.delete_object(
                Bucket=BUCKET,
                Key=local_files[0].replace('a', str(x))
            )
            s3_client.delete_object(
                Bucket=BUCKET,
                Key=F"subprefix1/subprefix2/{local_files[1].replace('b', str(x))}"
            )
        for x in range(1000, 2000):
            s3_client.delete_object(
                Bucket=BUCKET,
                Key=local_files[0].replace('a', str(x))
            )
            s3_client.delete_object(
                Bucket=BUCKET,
                Key=F"subprefix1/subprefix2/subprefix3/{local_files[1].replace('b', str(x))}"
            )

        s3_client.delete_bucket(
            Bucket=BUCKET
        )
        s3_client.delete_bucket(
            Bucket=BUCKET2
        )

    def test_copy_threaded(self):
        s3 = boto3.client('s3')
        input_prefix = f's3://{BUCKET}/subprefix1/'
        output_prefix = f's3://{BUCKET2}/somenewprefix/'
        results = copy_prefix_threaded(s3=s3, in_prefix=input_prefix, out_prefix=output_prefix, threads=10)
        expected_results = []
        for x in range(0, 1000):
            expected_results.append(f"s3://{BUCKET2}/somenewprefix/subprefix2/{local_files[1].replace('b', str(x))}")
        for x in range(1000, 2000):
            expected_results.append(f"s3://{BUCKET2}/somenewprefix/subprefix2/subprefix3/{local_files[1].replace('b', str(x))}")
        self.assertCountEqual(results, expected_results)

        # Clean up
        for path in expected_results:
            bucket, prefix = get_bucket_key(path)
            s3.delete_object(
                Bucket=bucket,
                Key=prefix
            )