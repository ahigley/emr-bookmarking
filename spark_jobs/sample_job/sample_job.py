from pyspark.sql import SparkSession
import argparse
import boto3
from bookmarking.utilities import get_bucket_key
import json
import os


def full_file_list(info: dict, prefixes: list):
    """
    Takes the list of desired prefixes and returns a full list of files based on previously generated run_info
    :param info: the rob run info dictionary
    :param prefixes: a list of prefixes e.g. ['s3://bucket/prefix/', 's3://bucket/prefix2/']
    :return: e.g. ['s3://bucket/prefix/file1.txt', 's3://bucket/prefix/file2.txt', 's3://bucket/prefix2/file3.txt']
    """
    all_files = []
    for prefix, details in info['cdc_files']:
        if prefix in prefixes:
            all_files.extend(details['files'])
    for prefix, details in info['full_files']:
        if prefix in prefixes:
            all_files.extend(details['files'])
    return all_files


def get_run_info(info_path: str, s3_client):
    run_info_bucket, run_info_prefix = get_bucket_key(info_path)
    s3_client.download_file(run_info_bucket, run_info_prefix, 'run_info.json')
    run_info_file = open('run_info.json', 'r')
    run_info = json.loads(run_info_file.read())

    # clean up
    run_info_file.close()
    os.remove('run_info.json')

    return run_info


def run(run_info_path, s3_client):

    run_info = get_run_info(run_info_path, s3_client)
    # Spark logic goes here
    spark = SparkSession.builder.appName("sample_job").getOrCreate()
    # full_file_list enables bookmarking logic and file tracking/saves you an s3 list
    df = spark.read.csv(full_file_list(run_info, ['s3://ahigley-emr/sample_data/']))
    df = df.dropDuplicates(subset=['id'])
    df.write.csv('s3://ahigley-emr/spark_outputs/')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_info", help="s3 location of the run info file")

    args = parser.parse_args()

    s3 = boto3.client('s3', region_name='us-east-1')
    run(args.run_info, s3)

