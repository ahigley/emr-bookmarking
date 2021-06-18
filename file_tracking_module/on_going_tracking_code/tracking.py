import boto3
import os
import time

# Example s3 event
# {
#   "Records": [
#     {
#       "eventVersion": "2.1",
#       "eventSource": "aws:s3",
#       "awsRegion": "us-east-2",
#       "eventTime": "2019-09-03T19:37:27.192Z",
#       "eventName": "ObjectCreated:Put",
#       "userIdentity": {
#         "principalId": "AWS:AIDAINPONIXQXHT3IKHL2"
#       },
#       "requestParameters": {
#         "sourceIPAddress": "205.255.255.255"
#       },
#       "responseElements": {
#         "x-amz-request-id": "D82B88E5F771F645",
#         "x-amz-id-2": "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
#       },
#       "s3": {
#         "s3SchemaVersion": "1.0",
#         "configurationId": "828aa6fc-f7b5-4305-8584-487c791949c1",
#         "bucket": {
#           "name": "lambda-artifacts-deafc19498e3f2df",
#           "ownerIdentity": {
#             "principalId": "A3I5XTEXAMAI3E"
#           },
#           "arn": "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
#         },
#         "object": {
#           "key": "b21b84d653bb07b05b1e6b33684dc11b",
#           "size": 1305107,
#           "eTag": "b21b84d653bb07b05b1e6b33684dc11b",
#           "sequencer": "0C0F6F405D6ED209E1"
#         }
#       }
#     }
#   ]
# }


def lambda_handler(event, context):
    dynamo = boto3.client('dynamodb')
    tracking_prefix = os.environ['prefix']
    table_name = os.environ['table_name']
    current_write_details = dynamo.query(
            TableName=table_name,
            Select='ALL_ATTRIBUTES',
            ConsistentRead=True,
            KeyConditionExpression=f'run_number = :run AND s3_path begins_with :pre',
            ExpressionAttributeValues={":run": {"S": "current_write"}, ":pre": {"S": "run"}},
        )
    current_write = current_write_details.get('s3_path', {}).get('S')
    if current_write:
        run_hash = current_write_details['run_hash']['S']
        for record in event['Records']:
            event_time = record['eventTime']
            pattern = '%Y-%m-%dT%H:%M:%S.%fZ'
            event_time_epoch = int(time.mktime(time.strptime(event_time, pattern)))
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            dynamo.put_item(
                TableName=table_name,
                Item={
                    'run_number': {
                        'S': run_hash
                    },
                    's3_path': {
                        'S': f"s3://{bucket}/{key}"
                    },
                    'event_time': {
                        'S': event_time
                    },
                    'event_time_epoch': {
                        'S': event_time_epoch
                    },
                    'run': {
                        'S': current_write
                    },
                    'prefix': {
                        'S': tracking_prefix
                    },
                    'bucket': {
                        'S': bucket
                    }
                },
            )


