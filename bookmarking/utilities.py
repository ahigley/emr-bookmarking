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


def full_file_list(info: dict, prefixes: list):
    """
    Takes the list of desired prefixes and returns a full list of files based on previously generated run_info
    :param info: the rob run info dictionary
    :param prefixes: a list of prefixes e.g. ['s3://bucket/prefix/', 's3://bucket/prefix2/']
    :return: e.g. ['s3://bucket/prefix/file1.txt', 's3://bucket/prefix/file2.txt', 's3://bucket/prefix2/file3.txt']
    """
    all_files = []
    for prefix, details in info['cdc_files']:
        if prefix in prefixes:
            all_files.extend(details['files'])
    for prefix, details in info['full_files']:
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
