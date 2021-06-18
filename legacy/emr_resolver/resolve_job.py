import boto3
import os
from legacy.bookmarking.utilities import get_bucket_key
from legacy.bookmarking.s3_copy import copy_prefix_threaded
import json
import re


def update_lambda(lambda_client, name, run_info):
    """
    Updates two lambda environment variables. The intention here is that the lambda always triggers the same ecs task
    but with one different input: 'last_run' which contain s3 path to what is now the current run, but by the next
    invocation will have been the last run
    file
    :param lambda_client: boto3 lambda client
    :param name: the name of the lambda function being updated
    :param run_info: the s3 path of the run_info for this particular run
    :return:
    """
    # Need to get current environment to avoid clobbering other variables which should not be changed
    response = lambda_client.get_function(
        FunctionName=name
    )
    env = response['Configuration']['Environment']
    env['Variables']['last_run'] = run_info
    lambda_client.update_function_configuration(
        FunctionName=name,
        Environment=env
    )


def upload_processed_info(s3_client, run_info, files, meta_data_prefix) -> None:
    """
    Uploads the copied (output) files information to a specified s3 location to enable the output portion of input
    and output file tracking
    :param s3_client: boto3 s3 client
    :param run_info: s3 path of the run info used as input, needed to extract the run number
    :param files: list of final file locations in s3
    :param meta_data_prefix: s3 prefix location where the output info file should be stored
    :return: None - simply a file upload
    """
    meta_bucket, meta_prefix = get_bucket_key(meta_data_prefix)
    run_info_file = run_info.split('/')[-1]
    match = re.search('_([0-9]+)\\.json', run_info_file)
    run_number = match.group(1)
    process_files = {'files': files}
    processed_file_name = f'output_run_{run_number}.json'
    processed_file = open(processed_file_name, 'w+')
    processed_file.write(json.dumps(process_files))
    processed_file.close()
    s3_client.upload_file(processed_file_name, meta_bucket, f'{meta_prefix}{processed_file_name}')
    os.remove(processed_file_name)


def run(temp_prefix, final_prefix, meta_data_prefix, s3_client, run_info, lambda_client, function_name):
    final_files = copy_prefix_threaded(s3=s3_client, in_prefix=temp_prefix, out_prefix=final_prefix, threads=20)
    upload_processed_info(s3_client=s3_client, run_info=run_info, files=final_files, meta_data_prefix=meta_data_prefix)
    update_lambda(lambda_client=lambda_client, name=function_name, run_info=run_info)


if __name__ == "__main__":
    s3 = boto3.client('s3', region_name='us-east-1')
    aws_lambda = boto3.client('lambda', region_name='us-east-1')
    # Required
    temp_path = os.environ['TEMP_PATH']
    final_path = os.environ['FINAL_PATH']
    meta_data_path = os.environ['META_DATA_PATH']
    run_info_path = os.environ['RUN_INFO_PATH']
    lambda_name = os.environ['LAMBDA']
    run(temp_prefix=temp_path, final_prefix=final_path, meta_data_prefix=meta_data_path, s3_client=s3,
        run_info=run_info_path, lambda_client=aws_lambda, function_name=lambda_name)
