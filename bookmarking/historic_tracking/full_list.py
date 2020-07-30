import boto3
from bookmarking.s3_list import s3_list, ListType
from bookmarking.utilities import chunk_files
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

PREFIX_TO_TRACK = 's3://ahigley-emr/sample_data/'
RUN_INFO = "run_0"
THREADS = 5
TABLE_NAME = "sample_job-file-tracking"


def update_dynamo(dynamo_client, table_name, paths):
    for path in paths:
        dynamo_client.put_item(
            TableName=table_name,
            Item={
                'run_number': {
                    'S': RUN_INFO
                },
                's3_path': {
                    'S': path
                },
                'prefix': {
                    'S': PREFIX_TO_TRACK
                }
            },
        )


def _run(s3_client, dynamo_client):
    files_to_track = s3_list(s3=s3_client, path=PREFIX_TO_TRACK, how=ListType.full)

    grouped_files = chunk_files(files_to_track, THREADS)

    with ThreadPoolExecutor(max_workers=THREADS, thread_name_prefix='dynamo_loader') as executor:
        all_futures = {executor.submit(update_dynamo, dynamo_client, TABLE_NAME, group) for group in
                       grouped_files}
        for future in as_completed(all_futures):  # wait
            future.result()


if __name__ == "__main__":
    dynamo = boto3.client('dynamodb', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    _run(s3_client=s3, dynamo_client=dynamo)