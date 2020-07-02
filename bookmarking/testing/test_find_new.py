import unittest
import boto3
from moto import mock_s3
import datetime
import pytz
from bookmarking.find_new_files import remove_common, find_latest, get_old_new
from bookmarking.s3_list import s3_list, ListType

# Needs to match the bucket in test_files/run_1.json
BUCKET = 'bucket1'
local_files = ['test_files/test_a.txt', 'test_files/test_b.txt', 'test_files/run_1.json']


class TestRemoveCommon(unittest.TestCase):
    def test_remove_common(self):
        needs_removal = [1, 2, 3, 4, 5, 6]
        to_remove = [2, 4, 5]
        result = remove_common(needs_removal, to_remove)
        expected_result = [1, 3, 6]
        self.assertCountEqual(result, expected_result)


@mock_s3
class TestFindLatest(unittest.TestCase):
    old_max = None

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
        s3_client.upload_file(local_files[0], BUCKET, 'prefix/file1.txt')
        s3_client.upload_file(local_files[0], BUCKET, 'prefix/file2.txt')
        # After the initial upload but before the new upload
        self.old_max = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

    def tearDown(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='prefix/file1.txt'
        )
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='prefix/file2.txt'
        )
        s3_client.delete_bucket(
            Bucket=BUCKET
        )

    def test_get_latest(self) -> None:
        s3_client = boto3.client('s3')
        old = s3_list(s3_client, f's3://{BUCKET}/prefix/', ListType.full)
        old_files = [x[0] for x in old]
        # A new upload to compare against our 'processed' files
        s3_client.upload_file(local_files[1], BUCKET, 'prefix/subprefix/file3.txt')
        new = s3_list(s3_client, f's3://{BUCKET}/prefix/', ListType.full)
        unprocessed, max_ts = find_latest(old_files, new, self.old_max.strftime('%Y-%m-%d %H:%M:%S.%f'))
        self.assertGreater(max_ts, self.old_max)
        self.assertEqual(len(unprocessed), 1)
        expected_unprocessed = [f's3://{BUCKET}/prefix/subprefix/file3.txt']
        self.assertCountEqual(unprocessed, expected_unprocessed)
        # Clean up
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='prefix/subprefix/file3.txt'
        )

    def test_get_old_new(self):
        s3_client = boto3.client('s3')
        s3_client.upload_file(local_files[2], BUCKET, 'run_1.json')
        old_path = f's3://{BUCKET}/run_1.json'
        cdc_paths = {"for_df_one": [f's3://{BUCKET}/prefix/']}
        s3_client.upload_file(local_files[1], BUCKET, 'prefix/subprefix/file3.txt')
        output = get_old_new(s3=s3_client, old_info=old_path, cdc_info=cdc_paths)
        expected_files = [f's3://{BUCKET}/prefix/subprefix/file3.txt']
        expected_complete = False
        expected_run_id = 2
        # Hard to test the expected max ts since it will depend on the time the test was run
        self.assertCountEqual(output['cdc_files']['for_df_one']['all_files'], expected_files)
        self.assertEqual(expected_complete, output['complete'])
        self.assertEqual(expected_run_id, output['run_id'])
        # Clean up
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='prefix/subprefix/file3.txt'
        )
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='run_1.json'
        )

    def test_first_run(self):
        s3 = boto3.client('s3')
        cdc_paths = {"some_new_df": [f's3://{BUCKET}/prefix/']}
        output = get_old_new(s3=s3, cdc_info=cdc_paths)
        expected_files = [f's3://{BUCKET}/prefix/file1.txt', f's3://{BUCKET}/prefix/file2.txt']
        expected_complete = False
        expected_run_id = 0
        self.assertCountEqual(output['cdc_files']['some_new_df']['all_files'], expected_files)
        self.assertEqual(expected_complete, output['complete'])
        self.assertEqual(expected_run_id, output['run_id'])
