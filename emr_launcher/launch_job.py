import argparse
import boto3
import os
from bookmarking.utilities import get_bucket_key
from bookmarking.s3_list import s3_list, ListType
from bookmarking.find_new_files import get_old_new
import json


def upload_start_job(script, spark_args, s3_client, job_name, job_run_full):
    """
    Uploads the strart_job.sh script which is responsible for starting the pyspark script
    :param package_path:
    :param script:
    :param spark_args:
    :param s3_client:
    :param job_name:
    :param job_run_full:
    :return:
    """

    start_job_file = open('scripts/start_job_template.sh', 'r')
    text = start_job_file.read().format(job_script=script,
                                        arguments=f"--run_info {job_run_full} {spark_args}")
    start_job_file.close()
    start_job = open('start_job.sh', 'w+')
    start_job.write(text)
    start_job.close()
    s3_client.upload_file('start_job.sh', 'ahigley-emr', f'{job_name}/job_bash_scripts/start_job.sh')
    os.remove('start_job.sh')


def upload_bootstrap(package_path, job_name, s3_client):
    """
    Uploads the boostrap.sh script to be used by the emr job during the bootstrap step
    :param package_path:
    :param job_name:
    :param s3_client:
    :return:
    """
    bucket, prefix = get_bucket_key(package_path)
    # package=prefix.split('/')[-1]
    bootstrap_file = open('scripts/bootstrap_template.sh', 'r')
    text = bootstrap_file.read().format(bucket=bucket, prefix=prefix, package=prefix.split('/')[-1])
    bootstrap_file.close()
    bootstrap = open('bootstrap.sh', 'w+')
    bootstrap.write(text)
    bootstrap.close()

    s3_client.upload_file('bootstrap.sh', 'ahigley-emr', f'{job_name}/job_bash_scripts/bootstrap.sh')
    os.remove('bootstrap.sh')


def upload_new_run_info(last_run, run_info_prefix, cdc_paths, full_paths, s3_client) -> str:
    """
    Uploads the new run info file to s3 to be used by the spark job downstream and returns the s3 path of the uploaded
    file
    :param last_run: The location of the specific last run info file, from a previous job run, if one exists
    :param run_info_prefix: The prefix where the current run info file will be stored, typically the prefix of
     the last_run location
    :param cdc_paths: A list of cdc prefixes to be included
    :param full_paths: A list of full load prefixes to be included
    :param s3_client: s3 boto3 client
    :return: The s3 path of the uploaded file
    """
    if last_run:
        this_run = get_old_new(s3=s3_client, old_info=last_run, cdc_prefixes=cdc_paths,
                               full_load_prefixes=full_paths)
    else:
        this_run = get_old_new(s3=s3_client, cdc_prefixes=cdc_paths, full_load_prefixes=full_paths)

    job_run_bucket, job_run_prefix = get_bucket_key(run_info_prefix)
    this_run_id = this_run['run_id']
    new_run_name = f'run_{this_run_id}.json'
    this_run_file = open(new_run_name, 'w+')
    this_run_file.write(json.dumps(this_run))
    this_run_file.close()

    this_job_run_key = f"{job_run_prefix}{new_run_name}"
    s3_client.upload_file(new_run_name, job_run_bucket, this_job_run_key)
    this_job_run_full_path = f's3://{job_run_bucket}/{this_job_run_key}'
    os.remove(new_run_name)
    return this_job_run_full_path


def start_emr(emr_path, s3_client, emr_client):
    """
    Starts the emr job that will run the pyspark logic
    :param emr_path:
    :param s3_client:
    :param emr_client:
    :return:
    """
    config_bucket, config_prefix = get_bucket_key(emr_path)
    s3_client.download_file(config_bucket, config_prefix, 'emr_details.json')
    emr_details_file = open('emr_details.json', 'r')
    emr_details = json.loads(emr_details_file.read())

    response = emr_client.run_job_flow(
        Name=emr_details['name'],
        LogUri=emr_details['log_location'],
        ReleaseLabel=emr_details['emr_version'],
        Instances=emr_details['instances'],
        Steps=emr_details['steps'],
        BootstrapActions=emr_details['bootstraps'],
        Applications=emr_details['applications'],
        Configurations=emr_details.get('configs'),
        VisibleToAllUsers=emr_details['visible_all_users'],
        JobFlowRole=emr_details['emr_ec2_role'],
        ServiceRole=emr_details['emr_service_role'],
        Tags=emr_details.get('tags')
    )
    return response


def run(emr_client, arguments, s3_client):
    inputs_bucket, inputs_prefix = get_bucket_key(arguments.inputs_file)
    s3_client.download_file(inputs_bucket, inputs_prefix, 'inputs.json')
    inputs_file = open('inputs.json', 'r')
    inputs = json.loads(inputs_file.read())
    os.remove('inputs.json')

    # Bookmarking/file tracking file
    this_job_run_full_path = upload_new_run_info(last_run=inputs.get('last_run'),
                                                 run_info_prefix=inputs['run_info_prefix'],
                                                 cdc_paths=inputs.get('cdc_paths'),
                                                 full_paths=inputs.get('full_paths'), s3_client=s3_client)

    # Shell script that runs spark-submit to start the spark job
    upload_start_job(script=inputs['script'], spark_args=inputs['spark_args'], s3_client=s3_client,
                     job_name=inputs['job_name'], job_run_full=this_job_run_full_path)
    # Shell script that installs requirements on all clusters
    upload_bootstrap(package_path=inputs['package'], job_name=inputs['job_name'], s3_client=s3_client)

    response = start_emr(emr_path=inputs['emr_details'], s3_client=s3_client, emr_client=emr_client)

    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--last_run", help="The s3 path containing information about the preceeding job run")
    parser.add_argument("--inputs_file", help="The s3 location of the inputs configuration file")
    args = parser.parse_args()
    emr = boto3.client('emr', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    run(emr, args, s3)
