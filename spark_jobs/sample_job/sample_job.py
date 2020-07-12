from pyspark.sql import SparkSession
import argparse
import boto3
from bookmarking.utilities import full_file_list, get_run_info
from bookmarking.trigger_resolver import run_resolver_lambda
import json
import os


def run(run_info_path, s3_client, lambda_client):

    run_info = get_run_info(run_info_path, s3_client)
    # Spark logic goes here
    spark = SparkSession.builder.appName("sample_job").getOrCreate()
    # full_file_list enables bookmarking logic and file tracking/saves you an s3 list
    df = spark.read.csv(full_file_list(run_info, ['s3://ahigley-emr/sample_data/']))
    df = df.dropDuplicates()
    df.write.save(path='s3://ahigley-emr/sample_job/temp_outputs/', format='csv', mode='append')

    # Job is done now resolve
    run_resolver_lambda(temp_prefix='s3://ahigley-emr/sample_job/temp_outputs/',
                        final_prefix='s3://ahigley-emr/sample_job/final_outputs/',
                        run_info=run_info_path,
                        # Crappy that you have to know this, maybe in future it will be passed to the job as an argument
                        function_name='resolver_trigger_lambda_sample_job',
                        lambda_client=lambda_client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_info", help="s3 location of the run info file")

    args = parser.parse_args()

    s3 = boto3.client('s3', region_name='us-east-1')
    aws_lambda = boto3.client('lambda', region_name='us-east-1')
    run(args.run_info, s3, aws_lambda)

