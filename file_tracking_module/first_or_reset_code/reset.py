import os
import boto3
import hashlib
import time
from datetime import datetime


def list_more(s3, bucket: str, prefix: str, token: typing.Optional[str] = None) -> dict:
    """

    :param s3: boto3 s3 client
    :param str bucket: the bucket being listed
    :param str prefix: the prefix to list under
    :param str token: the continuation token, if any
    :return dict: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_objects_v2
    """
    if token:
        response = s3.list_objects_v2(
            Bucket=bucket,
            MaxKeys=999,
            Prefix=prefix,
            ContinuationToken=token
        )
    else:
        response = s3.list_objects_v2(
            Bucket=bucket,
            MaxKeys=999,
            Prefix=prefix
        )
    return response


def handle_failures(dynamodb_client, table_name, failed, attempt):
    """

    :param dynamodb_client: boto3 dynamodb client
    :param table_name: the name of the dynamodb table where files are tracked
    :param failed: a list of items to write to the dynamodb table which failed
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.batch_write_item
    :param attempt: the current attempt number e.g. 2
    :return:
    """
    if attempt > 10:
        raise ValueError("Could not recover from failures")
    write_response = dynamodb_client.batch_write_item(
        RequestItems={table_name: failed}
    )
    new_failed = write_response.get('UnprocessedItems', {}).get(table_name, [])
    if len(new_failed) > 0:
        attempt = attempt + 1
        to_sleep = min(600, 2 ** attempt)
        time.sleep(to_sleep)
        return handle_failures(dynamodb_client, table_name, new_failed, attempt)
    else:
        return


def initial_tracking(s3_client, dynamo_client, table_name, s3_bucket, s3_prefix, run_number, run_hash):
    """

    :param s3_client: boto3 s3 client
    :param dynamo_client: boto3 dynamodb client
    :param table_name: the name of the dynamodb table where files are tracked
    :param s3_bucket: bucket being tracked
    :param s3_prefix: prefix being tracked
    :param run_number: the current run to write to e.g. run_3
    :param run_hash: the md5 hash of the current run number
    :return:
    """
    still_more = True
    continuation_token = None
    while still_more:
        response = list_more(s3_client, s3_bucket, s3_prefix, continuation_token)
        current_output = [F"s3://{s3_bucket}/{x['Key']}" for x in response['Contents'] if not x['Key'].endswith('/')]
        modified_output = []
        current_datetime = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
        current_epoch = int(time.time())
        for path in current_output:
            write_template = {
                'PutRequest': {
                    'Item': {
                        'run_number': {
                            'S': run_hash
                        },
                        's3_path': {
                            'S': path
                        },
                        'event_time': {
                            'S': current_datetime
                        },
                        'event_time_epoch': {
                            'N': f'{current_epoch}'
                        },
                        'run': {
                            'S': run_number
                        },
                        'prefix': {
                            'S': s3_prefix
                        },
                        'bucket': {
                            'S': s3_bucket
                        }
                    }
                }
            }
            modified_output.append(write_template)
        write_response = dynamo_client.batch_write_item(
            RequestItems={table_name: modified_output}
        )
        failed = write_response.get('UnprocessedItems', {}).get(table_name, [])
        if len(failed) > 0:
            handle_failures(dynamo_client, table_name, failed, 0)
        if response['IsTruncated']:
            continuation_token = response['NextContinuationToken']
        else:
            still_more = False


def run():
    """
    Initializes the dynamodb table with current_run and current_write information. Populates run_number with the hash
    of the current_run and s3_path with the s3 path of the files to process based on a complete listing of the prefix.
    :return:
    """
    _s3 = boto3.client('s3')
    _dynamo = boto3.client('dynamodb')
    prefix = os.environ['prefix']
    bucket = os.environ['bucket']
    table_name = os.environ['table_name']
    current_write_details = _dynamo.query(
            TableName=table_name,
            Select='ALL_ATTRIBUTES',
            ConsistentRead=True,
            KeyConditionExpression=f'run_number = :run AND s3_path begins_with :pre',
            ExpressionAttributeValues={":run": {"S": "current_write"}, ":pre": {"S": "run"}},
        )
    current_run_details = _dynamo.query(
            TableName=table_name,
            Select='ALL_ATTRIBUTES',
            ConsistentRead=True,
            KeyConditionExpression=f'run_number = :run AND s3_path begins_with :pre',
            ExpressionAttributeValues={":run": {"S": "current_run"}, ":pre": {"S": "run"}},
        )
    current_write = current_write_details.get('s3_path', {}).get('S')
    current_run = current_run_details.get('s3_path', {}).get('S')
    if current_write and current_run:
        run_num = int(current_run.split('_')[1])
        new_run_num = run_num + 1
        new_write_num = run_num + 2
    else:
        new_run_num = 0
        new_write_num = 1
    full_run = f'run_{new_run_num}'
    run_hash = hashlib.md5(full_run.encode('utf-8')).hexdigest()
    _dynamo.put_item(
        TableName=table_name,
        Item={
            'run_number': {
                'S': 'current_run'
            },
            's3_path': {
                'S': full_run
            },
            'attempt': {
                'N': '0'
            },
            'run_hash': {
                'S': run_hash
            },
            'prefix': {
                'S': prefix
            },
            'bucket': {
                'S': bucket
            }
        }
    )
    full_write = f'run_{new_write_num}'
    write_hash = hashlib.md5(full_write.encode('utf-8')).hexdigest()
    _dynamo.put_item(
        TableName=table_name,
        Item={
            'run_number': {
                'S': 'current_write'
            },
            's3_path': {
                'S': full_write
            },
            'run_hash': {
                'S': write_hash
            },
            'prefix': {
                'S': prefix
            },
            'bucket': {
                'S': bucket
            }
        }
    )
    initial_tracking(_s3, _dynamo, table_name, bucket, prefix, full_run, run_hash)


def test():
    print('hello world')


if __name__ == "__main__":
    # run()
    test()
