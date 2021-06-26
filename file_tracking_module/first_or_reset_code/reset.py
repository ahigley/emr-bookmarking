import os
import boto3
import hashlib
import time
from datetime import datetime
from botocore.exceptions import ClientError

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
            MaxKeys=1000,
            Prefix=prefix,
            ContinuationToken=token
        )
    else:
        response = s3.list_objects_v2(
            Bucket=bucket,
            MaxKeys=1000,
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


def initial_tracking_unlimited(s3_client, dynamo_client, info):
    """
    Populating on first run or reset where max count does not restrict the number of paths/run
    :param s3_client: boto3 s3 client
    :param dynamo_client: boto3 dynamodb client
    :param info: dict of info for populating table such as:
    table_name -> dynamodb table name
    bucket -> tracked bucket
    prefix -> tracked s3 prefix
    full_run -> run number (e.g. run_0)
    run_hash -> md5 hash of the full_run
    :return:
    """

    s3_bucket = info['bucket']
    s3_prefix = info['prefix']
    run_hash = info['run_hash']
    run_number = info['full_run']
    table_name = info['table_name']
    still_more = True
    continuation_token = None
    while still_more:
        response = list_more(s3_client, s3_bucket, s3_prefix, continuation_token)
        current_output = [F"s3://{s3_bucket}/{x['Key']}" for x in response['Contents'] if not x['Key'].endswith('/')]
        # 25 items is the max number per batch write in dynamodb
        batches = [current_output[x:x+25] for x in range(0, len(current_output), 25)]
        for batch in batches:
            modified_output = []
            current_datetime = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
            current_epoch = int(time.time())
            for path in batch:
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


def increment_current_run_write(dynamo, details):
    table_name = details['table_name']
    full_run = details['full_write']
    dynamo.put_item(
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
    dynamo.put_item(
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
            },
            'max_count': {
                'N': max_count
            }
        }
    )


def handle_transaction_failure():
    pass


def initial_tracking_restricted(s3_client, dynamo_client, info):
    """
    Populating on first run or reset where max count restricts number of paths/run
    :param s3_client: boto3 s3 client
    :param dynamo_client: boto3 dynamodb client
    :param info: dict of info for populating table such as:
    table_name -> dynamodb table name
    bucket -> tracked bucket
    prefix -> tracked s3 prefix
    full_run -> run number (e.g. run_0)
    run_hash -> md5 hash of the full_run
    max_count -> maximum number of items to include per run
    :return:
    """
    # details = {'table_name': table_name,
    #            'bucket': bucket,
    #            'prefix': prefix,
    #            'full_run': full_run,
    #            'run_hash': run_hash,
    #            'max_count': max_count,
    #            'full_write': full_write,
    #            'write_hash': write_hash}
    s3_bucket = info['bucket']
    s3_prefix = info['prefix']
    run_hash = info['run_hash']
    run_number = info['full_run']
    table_name = info['table_name']
    max_count = info['max_count']
    full_write = info['full_write']
    write_hash = info['write_hash']
    still_more = True
    continuation_token = None
    run_filled = False
    current_count = 0
    while still_more:
        response = list_more(s3_client, s3_bucket, s3_prefix, continuation_token)
        current_output = [F"s3://{s3_bucket}/{x['Key']}" for x in response['Contents'] if not x['Key'].endswith('/')]
        # 25 items is the max number per batch write in dynamodb
        batches = [current_output[x:x+25] for x in range(0, len(current_output), 25)]
        for batch in batches:
            if current_count >= max_count:
                run_filled = True
            current_datetime = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
            current_epoch = int(time.time())
            # After reset or initial start we are pointing to the current_run -> after this reaches max_count
            # we have to compete with the on going lambda so the logic is different
            if not run_filled:
                modified_output = []
                for path in batch:
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
                current_count = current_count + len(batch)
            else:
                # Here we use the write_hash because we are no longer on the first item to be run
                # functionality is roughly the same as the on going lambda
                for path in batch:
                    try:
                        current_item = [
                                {
                                    'Update': {
                                        'TableName': table_name,
                                        'Key': {
                                            'run_number': {
                                                'S': write_hash
                                            },
                                            's3_path': {
                                                'S': 'current_count'
                                            },
                                            'ConditionExpression': '#count < :max',
                                            'UpdateExpression': 'SET #count = #count + :inc',
                                            'ExpressionAttributeNames': {
                                                '#count': 'current_count'
                                            },
                                            'ExpressionAttributeValues': {
                                                ':inc': {'N': '1'},
                                                ':max': {'N': f'{max_count}'}
                                            }
                                        }
                                    },

                                    'Put': {
                                        'TableName': table_name,
                                        'Key': {
                                            'run_number': {
                                                'S': write_hash
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
                            ]
                        write_response = dynamo_client.transact_write_items(
                            TrasnsactItems=current_item
                        )
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'ConditionalCheckFailed':
                            # TODO make the the increment method
                            write_hash = increment_current_write(dynamo_client)
                            # TODO Okay now it's incremented we need to retry - how to do that?
                            # TODO Okay we retried - what if there is a provisioned throughput error?
                        elif e.response['Error']['Code'] == 'ProvisionedThroughputExceeded':
                            handle_transaction_failure(dynamo_client, current_item)
                        elif e.response['Error']['Code'] == 'ThrottlingError':
                            handle_transaction_failure(dynamo_client, current_item)
                        else:
                            print(str(e))
                            raise e

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
    max_count = os.environ['max_count']
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
        new_run_num = run_num + 2
        new_write_num = run_num + 3
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
            },
            'max_count': {
                'N': max_count
            }
        }
    )
    details = {'table_name': table_name,
               'bucket': bucket,
               'prefix': prefix,
               'full_run': full_run,
               'run_hash': run_hash,
               'max_count': max_count,
               'full_write': full_write,
               'write_hash': write_hash}

    if int(max_count) > 0:
        initial_tracking_restricted(_s3, _dynamo, details)
    else:
        initial_tracking_unlimited(_s3, _dynamo, details)


def test():
    print('hello world')


if __name__ == "__main__":
    # run()
    test()
