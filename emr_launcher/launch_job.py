import argparse
import boto3
import os
from bookmarking.utilities import get_bucket_key
from bookmarking.s3_list import s3_list, ListType
from bookmarking.find_new_files import get_old_new
import json


def upload_start_job(package_path, script, spark_args, s3_client, job_name, job_run_full):
    bucket, prefix = get_bucket_key(package_path)

    start_job_file = open('scripts/start_job_template.sh', 'r')
    text = start_job_file.read().format(bucket=bucket, prefix=prefix,
                                        package=prefix.split('/')[-1], job_script=script,
                                        arguments=f"--run_info {job_run_full} {spark_args}")
    start_job_file.close()
    start_job = open('start_job.sh', 'w+')
    start_job.write(text)
    start_job.close()
    s3_client.upload_file('start_job.sh', 'ahigley-emr', f'{job_name}/job_bash_scripts/start_job.sh')
    os.remove('start_job.sh')


def upload_bootstrap(requirements_path, job_name, s3_client):
    bucket, prefix = get_bucket_key(requirements_path)

    bootstrap_file = open('scripts/bootstrap_template.sh', 'r')
    text = bootstrap_file.read().format(bucket=bucket, prefix=prefix)
    bootstrap_file.close()
    bootstrap = open('bootstrap.sh', 'w+')
    bootstrap.write(text)
    bootstrap.close()

    s3_client.upload_file('bootstrap.sh', 'ahigley-emr', f'{job_name}/job_bash_scripts/bootstrap.sh')
    os.remove('bootstrap.sh')


def upload_new_run_info(inputs, s3_client) -> str:
    if inputs['last_run']:
        this_run = get_old_new(s3=s3_client, old_info=inputs['last_run'], cdc_info=inputs['cdc_info'],
                               full_load_info=inputs['full_info'])
    else:
        this_run = get_old_new(s3=s3_client, cdc_info=inputs['cdc_info'], full_load_info=inputs['full_info'])

    job_run_bucket, job_run_key = get_bucket_key(inputs['last_run'])
    this_run_id = this_run['run_id']
    new_run_name = f'run_{this_run_id}.json'
    this_run_file = open(new_run_name, 'w+')
    this_run_file.write(json.dumps(this_run))
    this_run_file.close()

    job_run_prefix = '/'.join(job_run_key.split('/')[:-1])
    this_job_run_key = f"{job_run_prefix}/{new_run_name}"
    s3_client.upload_file(new_run_name, job_run_bucket, this_job_run_key)
    this_job_run_full_path = f's3://{job_run_bucket}/{this_job_run_key}'
    return this_job_run_full_path


def run(emr_client, arguments, s3_client):
    inputs_bucket, inputs_prefix = get_bucket_key(arguments.inputs_file)
    s3_client.download_file(inputs_bucket, inputs_prefix, 'inputs.json')
    inputs_file = open('inputs.json', 'r')
    inputs = json.loads(inputs_file.read())

    this_job_run_full_path = upload_new_run_info(inputs, s3_client)

    upload_start_job(inputs['package'], inputs['script'], inputs['spark_args'], s3_client,
                     inputs['job_name'], this_job_run_full_path)
    upload_bootstrap(inputs['requirements'], inputs['job_name'], s3_client)

    emr_details_path = inputs['job_details']
    config_bucket, config_prefix = get_bucket_key(emr_details_path)
    s3_client.download_file(config_bucket, config_prefix, 'emr_details.json')
    emr_details_file = open('emr_details.json', 'r')
    emr_details = json.loads(emr_details_file.read())

    response = emr_client.run_job_flow(
        Name=emr_details['name'],
        LogUri=emr_details['log_location'],
        ReleaseLabel=emr_details['emr_version'],
        Instances=emr_details['instances'],
        Steps=emr_details['steps'],
        BootstrapActions=emr_details['bootstrap'],
        Applications=emr_details['applications'],
        Configurations=emr_details['configs'],
        VisibleToAllUsers=emr_details['visible_all_users'],
        JobFlowRole=emr_details['emr_ec2_role'],
        ServiceRole=emr_details['emr_service_role'],
        Tags=emr_details.get('tags')
    )
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--last_run", help="The s3 path containing information about the preceeding job run")
    parser.add_argument("--inputs_file", help="The s3 location of the inputs configuration file")
    args = parser.parse_args()
    emr = boto3.client('emr', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    run(emr, args, s3)
