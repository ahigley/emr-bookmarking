from botocore.errorfactory import ClientError
import json
import os


def get_bucket_key(path: str):
    """
    Takes a full s3 path and returns the bucket and prefix only
    :param path: e.g. s3://bucket/someprefix/somesubprefix/somefile.txt
    :return: bucket: bucket prefix: someprefix/somesubprefix/somefile.txt
    """
    path_parts = path.split('/')
    bucket = path_parts[2]
    key = '/'.join(path_parts[3:])
    return bucket, key


def s3_key_exists(bucket, key, s3):
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
    return True


def full_file_list(info: dict, prefixes: list):
    """
    Takes the list of desired prefixes and returns a full list of files based on previously generated run_info
    :param info: the rob run info dictionary
    :param prefixes: a list of prefixes e.g. ['s3://bucket/prefix/', 's3://bucket/prefix2/']
    :return: e.g. ['s3://bucket/prefix/file1.txt', 's3://bucket/prefix/file2.txt', 's3://bucket/prefix2/file3.txt']
    """
    all_files = []
    for prefix, details in info['cdc_files'].items():
        if prefix in prefixes:
            all_files.extend(details['files'])
    for prefix, details in info['full_load_files'].items():
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


def chunk_files(paths, num_groups):
    """
    Given a list of paths e.g. ['s3://bucket/prefix/file1.txt', ..., 's3://bucket/prefix/file10.txt'] a number of groups
    e.g. 5 returns a list of number of groups lists
    e.g. [['s3://bucket/prefix/file1.txt', 's3://bucket/prefix/file2.txt'], ...]
    :param paths:
    :param num_groups:
    :return:
    """

    import math
    if not paths:
        return None
    grouping = math.floor(len(paths)/num_groups)
    # Can't have groups of zero
    if grouping == 0:
        grouping = 1
    grouped_files = [paths[x: x + grouping] for x in range(0, len(paths), grouping)]

    return grouped_files


def get_current_result_set_dynamo(run_number, prefix, table_name, index, dynamodb_client, start_key):
    if start_key:
        return dynamodb_client.query(
            TableName=table_name,
            IndexName=index,
            Select='ALL_ATTRIBUTES',
            ConsistentRead=True,
            KeyConditionExpression=f'run_number = :run AND prefix = :pre',
            ExpressionAttributeValues={":run": {"S": run_number}, ":pre": {"S": prefix}},
            ExclusiveStartKey=start_key
        )
    else:
        return dynamodb_client.query(
            TableName=table_name,
            IndexName=index,
            Select='ALL_ATTRIBUTES',
            ConsistentRead=True,
            KeyConditionExpression=f'run_number = :run AND prefix = :pre',
            ExpressionAttributeValues={":run": {"S": run_number}, ":pre": {"S": prefix}}
        )


def get_files_for_prefix_run(run_number, prefix, table_name, index, dynamodb_client):
    start_key = None
    more = True
    results = []
    while more:
        response = get_current_result_set_dynamo(run_number, prefix, table_name, index, dynamodb_client, start_key)
        results.extend([x['s3_path']['S'] for x in response['Items']])
        start_key = response.get('LastEvaluatedKey')
        more = start_key
    return results


def get_files_for_prefixes(run_number, table_name, index, dynamodb_client, prefixes):
    all_files = []
    for prefix in prefixes:
        all_files.extend(get_files_for_prefix_run(run_number=run_number, prefix=prefix, table_name=table_name,
                                                  index=index, dynamodb_client=dynamodb_client))
    return all_files
