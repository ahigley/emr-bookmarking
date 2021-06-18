import unittest
import boto3
from moto import mock_s3
import os
from legacy.bookmarking.utilities import s3_key_exists
from legacy.emr_launcher.launch_job import upload_start_job, upload_bootstrap, upload_new_run_info
# Needs to match the bucket in test_files/run_1.json
BUCKET = 'ahigley-emr'


@mock_s3
class TestUploads(unittest.TestCase):

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
        s3_client.upload_file('../../dummy_data/file1.csv', BUCKET, 'sample_data/file1.csv')

    def tearDown(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='sample_data/file1.csv'
        )
        s3_client.delete_bucket(
            Bucket=BUCKET
        )

    def test_upload_start(self) -> None:
        s3_client = boto3.client('s3')
        script = 'spark_job.py'
        spark_args = "--date 2020-01-01 --target s3://bucket2/prefix/"
        job_name = 'sample_job'
        job_run_full = f's3://{BUCKET}/run_info/sample_job/run_1.json'
        upload_start_job(script=script, spark_args=spark_args, s3_client=s3_client, job_run_full=job_run_full,
                         launch_path=f's3://{BUCKET}/sample_job/job_bash_scripts/')
        self.assertTrue(s3_key_exists(BUCKET, 'sample_job/job_bash_scripts/start_job.sh', s3_client))
        expected_text = """#!/bin/bash

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

    def test_upload_bootstrap(self):
        s3_client = boto3.client('s3')
        package_path = F's3//{BUCKET}/sample_job/prefix/package.zip'
        upload_bootstrap(package_path=package_path, launch_prefix='s3://ahigley-emr/sample_job/job_bash_scripts/',
                         s3_client=s3_client)
        self.assertTrue(s3_key_exists(BUCKET, 'sample_job/job_bash_scripts/bootstrap.sh', s3_client))
        expected_text = """#!/bin/bash -x

aws s3 cp s3://ahigley-emr/sample_job/prefix/package.zip $HOME/
unzip -o $HOME/package.zip -d $HOME

sudo pip-3.7 install -r $HOME/requirements.txt"""
        s3_client.download_file(BUCKET, 'sample_job/job_bash_scripts/bootstrap.sh', 'result.txt')
        result_file = open('result.txt', 'r')
        result = result_file.read()
        self.assertEqual(expected_text, result)
        result_file.close()
        # Clean up
        os.remove('result.txt')
        s3_client.delete_object(
            Bucket=BUCKET,
            Key='sample_job/job_bash_scripts/bootstrap.sh'
        )

    def test_upload_first_run_info(self):
        last_run = None
        run_info_prefix = 's3://ahigley-emr/test_job/run_info/'
        cdc_paths = ['s3://ahigley-emr/sample_data/']
        full_paths = []
        s3 = boto3.client('s3')
        run_info_path = upload_new_run_info(last_run=last_run, cdc_paths=cdc_paths, full_paths=full_paths,
                                            s3_client=s3, run_info_prefix=run_info_prefix)
        expected_run_info_path = 's3://ahigley-emr/test_job/run_info/run_0.json'
        self.assertEqual(run_info_path, expected_run_info_path)

        # Clean up
        s3.delete_object(Bucket='ahigley-emr', Key='test_job/run_info/run_0.json')

    def test_upload_second_run_info(self):
        first_run = None
        run_info_prefix = 's3://ahigley-emr/test_job/run_info/'
        cdc_paths = ['s3://ahigley-emr/sample_data/']
        full_paths = []
        s3 = boto3.client('s3')
        first_run_info_path = upload_new_run_info(last_run=first_run, cdc_paths=cdc_paths, full_paths=full_paths,
                                                  s3_client=s3, run_info_prefix=run_info_prefix)
        expected_run_info_path = 's3://ahigley-emr/test_job/run_info/run_0.json'
        self.assertEqual(first_run_info_path, expected_run_info_path)
        s3.upload_file('../../dummy_data/file2.csv', BUCKET, 'sample_data/file2.csv')
        last_run = expected_run_info_path
        second_run_info_path = upload_new_run_info(last_run=last_run, cdc_paths=cdc_paths, full_paths=full_paths,
                                                   s3_client=s3, run_info_prefix=run_info_prefix)
        expected_second_run_info_path = 's3://ahigley-emr/test_job/run_info/run_1.json'
        self.assertEqual(expected_second_run_info_path, second_run_info_path)

        # Clean up
        s3.delete_object(Bucket='ahigley-emr', Key='test_job/run_info/run_0.json')
        s3.delete_object(Bucket='ahigley-emr', Key='test_job/run_info/run_1.json')
        s3.delete_object(Bucket='ahigley-emr', Key='sample_data/file2.csv')


# @mock_s3
# @mock_emr
# class TestEmrLaunch(unittest.TestCase):
#
#     def setUp(self) -> None:
#         s3_client = boto3.client(
#             's3',
#             region_name='us-east-1',
#             aws_access_key_id="fake",
#             aws_secret_access_key="fake_secret"
#         )
#         s3_client.create_bucket(
#             ACL='private',
#             Bucket=BUCKET
#         )
#
#     def tearDown(self) -> None:
#         s3_client = boto3.client(
#             's3',
#             region_name='us-east-1',
#             aws_access_key_id="fake",
#             aws_secret_access_key="fake_secret"
#         )
#         s3_client.delete_bucket(
#             Bucket=BUCKET
#         )
#
