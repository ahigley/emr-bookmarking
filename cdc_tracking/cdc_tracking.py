import boto3
import os


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
    dynamo = boto3.client('dynamodb', region_name='us-east-1')
    table_name = os.environ['table_name']
    response = dynamo.query(
        TableName=table_name,
        Select='ALL_ATTRIBUTES',
        ConsistentRead=True,
        KeyConditionExpression=f'run_number = :run AND s3_path BEGINS_WITH :path',
        ExpressionAttributeValues={":run": {"S": 'current_write'}, ":pre": {"S": 'run'}}
    )
    items = response.get('Items')
    if items:
        run_number = items[0]['s3_path']['S']
        run_hash = items[0]['run_hash']['S']
        prefix = items[0]['prefix']['S']
        for record in event['Records']:
            event_time = record['eventTime']
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            dynamo.put_item(
                TableName=table_name,
                Item={
                    'run_hash': {
                        'S': run_hash
                    },
                    's3_path': {
                        'S': f"s3://{bucket}/{key}"
                    },
                    'prefix': {
                        'S': F"s3://{bucket}/{prefix}"
                    },
                    'run': {
                        'S': run_number
                    },
                    'event_time': {
                        'S': event_time
                    }
                },
            )
    else:
        print('No items found for current_write. Have you performed initial setup on the dynamodb table?')
