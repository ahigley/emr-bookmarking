from bookmarking.s3_list import s3_list, ListType
from bookmarking.utilities import get_bucket_key
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from botocore.exceptions import ClientError
import math
from time import sleep
import typing


def copy_prefix_threaded(s3, in_prefix, out_prefix, threads):
    """
    Given an s3 input prefix and output prefix, copies all files in the input prefix to the output prefix using the
    specified number of threads. Returns a list of final file locations.
    :param s3: boto3 s3 client
    :param in_prefix: e.g. 's3://bucket/prefix/'
    :param out_prefix: e.g. 's3://bucket2/prefix2/'
    :param threads: e.g. 10
    :return: e.g. ['s3://bucket2/prefix2/file1.txt', 's3://bucket2/prefix2/file2.txt']
    """

    files_to_copy = [x[0] for x in s3_list(s3, in_prefix, ListType.prefix)]
    if not files_to_copy:
        return None
    grouping = math.floor(len(files_to_copy)/threads)
    # Can't have groups of zero
    if grouping == 0:
        grouping = 1
    grouped_files = [files_to_copy[x: x + grouping] for x in range(0, len(files_to_copy), grouping)]

    copied_files = []
    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix='s3_copier') as executor:
        all_futures = {executor.submit(s3_copy, files, in_prefix, out_prefix, s3, 5) for files in
                       grouped_files}
        for future in as_completed(all_futures):  # wait

            batch_copied = future.result()
            copied_files.extend(batch_copied)

    return copied_files


def s3_copy(items: list, input_prefix: str, output_prefix: str, s3_client, retries: int):
    """
    Given a list of files to be copied, returns a list of the final locations of the copied files after performing
    the copying
    :param items: e.g. ['s3://bucket/prefix/file1.txt', 's3://bucket/prefix/file2.txt']
    :param input_prefix: e.g. 's3://bucket/prefix/'
    :param output_prefix: e.g. 's3://bucket2/prefix2/'
    :param s3_client: boto3 s3 client
    :param retries: e.g. 5
    :return: e.g. ['s3://bucket2/prefix2/file1.txt', 's3://bucket2/prefix2/file2.txt']
    """
    in_bucket, in_prefix = get_bucket_key(input_prefix)
    out_bucket, out_prefix = get_bucket_key(output_prefix)
    new_files = []
    for s3_key in items:
        result = individual_copy_file(file=s3_key, input_prefix=in_prefix, output_prefix=out_prefix,
                                      input_bucket=in_bucket, output_bucket=out_bucket, s3_client=s3_client,
                                      max_retries=retries)
        new_files.append(result)
    return new_files


def individual_copy_file(file: str, input_prefix: str, output_prefix: str, input_bucket: str, output_bucket: str,
                         s3_client, max_retries: int, current_retries: typing.Optional[int] = 0):
    """
    Copies individual files, intended as a helper method to s3_copy. Includes exponential slow down logic in the case
    of exceeding s3 limits
    :param file: The file to be copied e.g. 's3://bucket/prefix/subprefix/file.txt'
    :param input_prefix: The prefix of the file to be copied e.g. 'prefix/'
    :param output_prefix: The prefix where the file should be copied to e.g. 'prefix2/'
    :param input_bucket: The bucket of the file to be copied e.g. 'bucket'
    :param output_bucket: The bucket where the file will be copied to e.g. 'bucket2'
    :param s3_client: boto3 s3 client
    :param max_retries: Maximum number of desired retries
    :param current_retries: Number of retries attempted so far
    :return: e.g. 's3://bucket2/prefix2/subprefix/file.txt'
    """
    if current_retries >= max_retries:
        raise ValueError(F"Maximum number of retries = {max_retries} has been exceeded.")
    try:
        source_key = file
        output_key = file.replace(input_prefix, output_prefix)

        copy_source = {'Bucket': input_bucket,
                       'Key': source_key}
        s3_client.copy(copy_source, output_bucket, output_key)
        return f"s3://{output_bucket}/{output_key}"
    except ClientError as e:
        if e.response['Error']['Code'] == 'SlowDown':
            sleep_length = (2 ** current_retries) * 5
            sleep(sleep_length)
            current_retries = current_retries + 1
            individual_copy_file(file=file, input_prefix=input_prefix, output_prefix=output_prefix,
                                 input_bucket=input_bucket, output_bucket=output_bucket, s3_client=s3_client,
                                 max_retries=max_retries, current_retries=current_retries)
        else:
            raise e
