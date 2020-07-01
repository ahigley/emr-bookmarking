import unittest
import boto3
from moto import mock_s3
import datetime
import pytz
import os
from bookmarking.utilities import s3_key_exists
from emr_launcher.launch_job import upload_start_job, upload_bootstrap, run
# Needs to match the bucket in test_files/run_1.json
BUCKET = 'ahigley-emr'


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
        self.assertTrue(s3_key_exists(BUCKET, 'sample_job/job_bash_scripts/start_job.sh', s3_client))
        expected_text = """#!/bin/bash

aws s3 cp s3://ahigley-emr/sample_job/prefix/package.zip $HOME/
unzip -o $HOME/package.zip -d $HOME

export PYSPARK_PYTHON="/usr/bin/python3"

/usr/bin/spark-submit --master yarn-client $HOME/spark_job.py --run_info s3://ahigley-emr/run_info/sample_job/run_1.json --date 2020-01-01 --target s3://bucket2/prefix/
"""
        s3_client.download_file(BUCKET, 'sample_job/job_bash_scripts/start_job.sh', 'result.txt')
        result_file = open('result.txt', 'r')
        result = result_file.read()
        self.assertEqual(expected_text, result)
        result_file.close()
        # Clean up
        os.remove('result.txt')
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='sample_job/job_bash_scripts/start_job.sh'
        )