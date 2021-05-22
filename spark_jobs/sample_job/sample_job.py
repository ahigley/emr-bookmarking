from pyspark.sql import SparkSession
import argparse
import boto3
from bookmarking.utilities import full_file_list, get_files_for_prefixes
from bookmarking.trigger_resolver import run_resolver_lambda
import json
import os


def run(run_number, table_name, index, dynamo):

    # Spark logic goes here
    spark = SparkSession.builder.appName("sample_job").getOrCreate()
    # get_files_for_prefixes enables bookmarking logic and file tracking/saves you an s3 list
    df = spark.read.csv(get_files_for_prefixes(run_number=run_number, table_name=table_name, index=index,
                                               dynamodb_client=dynamo, prefixes=['s3://ahigley-emr/sample_data/']))
    df = df.dropDuplicates()
    df.write.save(path='s3://ahigley-emr/sample_job/temp_outputs/', format='csv', mode='append')

    # Job is done now resolve
    run_resolver_lambda(temp_prefix='s3://ahigley-emr/sample_job/temp_outputs/',
                        final_prefix='s3://ahigley-emr/sample_job/final_outputs/',
                        run_info=run_info_path,
                        # Crappy that you have to know this, maybe in future it will be passed to the job as an argument
                        function_name='resolver_trigger_lambda_sample_job',
                        lambda_client=lambda_client)

    # cluster emr - bookmarking - cluster
    # final_prefix s3: // ahigley - emr / sample_job / final_outputs /
    # launcher_function launcher_trigger_lambda_sample_job
    # meta_data_prefix s3: // ahigley - emr / sample_job / run_info / output /
    # resolver sample_job_resolver
    # run_info s3: // ahigley - emr / test_job / run_info / run_4.json
    # subnet subnet - 0a8066232827443de, subnet - 0424375998fc31186
    # temp_prefix s3: // ahigley - emr / sample_job / temp_outputs /


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_info", help="name of the current run")
    parser.add_argument("--table_name", help="Name of the dynamodb table containing file tracking info for this job")
    parser.add_argument("--index", help="Name of the prefix index for the dynamoDB table with file tracking info")

    args = parser.parse_args()
    dynamo_client = boto3.client('dynamodb')
    run(run_number=args.run_info, table_name=args.table_name, index=args.index, dynamo=dynamo_client)
