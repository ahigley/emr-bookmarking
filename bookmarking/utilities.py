

def get_bucket_prefix(path: str):
    """
    Takes a full s3 path and returns the bucket and prefix only
    :param path: e.g. s3://bucket/someprefix/somesubprefix/somefile.txt
    :return: bucket: bucket prefix: someprefix/somesubprefix/somefile.txt
    """
    path_parts = path.split('/')
    bucket = path_parts[2]
    prefix = '/'.join(path_parts[3:])
    return bucket, prefix