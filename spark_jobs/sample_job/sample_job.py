from pyspark.sql import SparkSession
import argparse
import boto3
from bookmarking.utilities import full_file_list, get_run_info
import json
import os


def run(run_info_path, s3_client):

    run_info = get_run_info(run_info_path, s3_client)
    # Spark logic goes here
    spark = SparkSession.builder.appName("sample_job").getOrCreate()
    # full_file_list enables bookmarking logic and file tracking/saves you an s3 list
    df = spark.read.csv(full_file_list(run_info, ['s3://ahigley-emr/sample_data/']))
    df = df.dropDuplicates()
    df.write.save(path='s3://ahigley-emr/spark_outputs/', format='csv', mode='append')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_info", help="s3 location of the run info file")

    args = parser.parse_args()

    s3 = boto3.client('s3', region_name='us-east-1')
    run(args.run_info, s3)

