from botocore.errorfactory import ClientError

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
