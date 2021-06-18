import boto3
from legacy.bookmarking import s3_list, ListType
from legacy.bookmarking.utilities import chunk_files
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import os


def update_dynamo(dynamo_client, table, prefix, run, paths):
    for path in paths:
        dynamo_client.put_item(
            TableName=table,
            Item={
                'run_number': {
                    'S': run
                },
                's3_path': {
                    'S': path
                },
                'prefix': {
                    'S': prefix
                }
            },
        )


def _run(s3_client, dynamo_client, prefix, run, threads, table):
    files_to_track = s3_list(s3=s3_client, path=prefix, how=ListType.full)

    grouped_files = chunk_files(files_to_track, threads)

    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix='dynamo_loader') as executor:
        all_futures = {executor.submit(update_dynamo, dynamo_client, table, prefix, run, group) for group in
                       grouped_files}
        for future in as_completed(all_futures):  # wait
            future.result()


if __name__ == "__main__":
    # PREFIX_TO_TRACK = 's3://ahigley-emr/sample_data/'
    # RUN_INFO = "run_0"
    # THREADS = 5
    # TABLE_NAME = "sample_job-file-tracking"
    prefix_to_track = os.environ['PREFIX_TO_TRACK']
    run_info = os.environ['RUN_INFO']
    num_threads = os.environ['NUM_THREADS']
    table_name = os.environ['TABLE_NAME']
    dynamo = boto3.client('dynamodb', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    _run(s3_client=s3, dynamo_client=dynamo, prefix=prefix_to_track, run=run_info, threads=num_threads,
         table=table_name)