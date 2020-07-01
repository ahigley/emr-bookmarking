import unittest
import boto3
from moto import mock_s3
import datetime
import pytz
from bookmarking.find_new_files import remove_common, find_latest, get_old_new
from bookmarking.s3_list import s3_list, ListType
from emr_launcher.launch_job import upload_start_job, upload_bootstrap, run
# Needs to match the bucket in test_files/run_1.json
BUCKET = 'bucket1'


@mock_s3
class TestUploadStartJob(unittest.TestCase):

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

    def tearDown(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        s3_client.delete_bucket(
            Bucket=BUCKET
        )

    def test_upload_start(self) -> None:
        s3_client = boto3.client('s3')
        package_path = F's3//{BUCKET}/sample_job/prefix/package.zip'
        script = 'spark_job.py'
        spark_args = "--date 2020-01-01 --target s3://bucket2/prefix/"
        job_name = 'sample_job'
        job_run_full = f's3://{BUCKET}/run_info/sample_job/run_1.json'
        upload_start_job(package_path, script, spark_args, s3_client, job_name, job_run_full)
        self.
        # Clean up
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='prefix/subprefix/file3.txt'
        )