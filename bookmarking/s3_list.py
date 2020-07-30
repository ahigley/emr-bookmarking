import typing
import pytz
import enum
from bookmarking.utilities import get_bucket_key


class ListType(enum.Enum):
    # e.g. s3://bucket/prefix/file.txt
    full = 1
    # e.g. prefix/file.txt
    prefix = 2
    # e.g. file.txt
    object_only = 3


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


def s3_list(s3, path: str, how: typing.Optional[ListType] = ListType.full) -> list:
    """

    :param how: full -> s3://bucket/prefix/file.txt (default) | prefix -> prefix/file.txt | object_only -> file.txt
    :param s3: boto3 s3 client
    :param str path: the s3 path to list e.g. s3://bucket/prefix/subprefix/
    :return list: s3 objects
    """
    bucket, prefix = get_bucket_key(path)
    still_more = True
    continuation_token = None
    output = []
    while still_more:
        response = list_more(s3, bucket, prefix, continuation_token)
        if how == ListType.full:
            current_output = [F"s3://{bucket}/{x['Key']}" for x in response['Contents'] if not x['Key'].endswith('/')]
        elif how == ListType.prefix:
            current_output = [x['Key'] for x in response['Contents'] if not x['Key'].endswith('/')]
        elif how == ListType.object_only:
            current_output = [x['Key'].split('/')[-1] for x in response['Contents'] if not x['Key'].endswith('/')]
        else:
            raise ValueError('how must be specified as one of a valid ListType')
        output.extend(current_output)
        if response['IsTruncated']:
            continuation_token = response['NextContinuationToken']
        else:
            still_more = False

    return output
