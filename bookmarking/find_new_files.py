import datetime
import pytz
import typing
import json
from bookmarking.utilities import get_bucket_key
from bookmarking.s3_list import s3_list, ListType


# https://stackoverflow.com/questions/2514961/remove-all-values-within-one-list-from-another-list
# This is the fastest way
def remove_common(first: list, second: list):
    """
    Returns a list containing elements that exist in the first list but not the second. Assumes each item in the list is
    unique
    :param first: e.g. ['a', 'b', 'c']
    :param second: e.g. ['b']
    :return: e.g. ['a', 'c']
    """
    return list(set(first)-set(second))


def find_latest(old: list, new: list, since: str):
    """
    In general if objects are written infrequently only new items filtered by date time should be included
    However we can't be sure of two objects written at the same time so to be safe we subtract any old objects
    from the new list of objects as well
    :param old: list of old objects e.g. ['s3://bucket/key1', 's3://bucket/key2', ...]
    :param new: list from s3 with keys and last modified times e.g. [('key1', datetime(2020, 01, 01)), ...]
    :param since: str timestamp of the max last modified from old %Y-%m-%d %H:%M:%S.%f
    :return:
    """
    min_date = datetime.datetime.strptime(since, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.UTC)
    filtered_new = [x[0] for x in new if x[1] > min_date]
    max_date = max([x[1] for x in new])
    return remove_common(filtered_new, old), max_date


def get_old_new(s3, cdc_paths: list, old_info: typing.Optional[str] = None):
    """
    Gets the list of objects of old and new and compares them. Returns a dictionary that conforms to the old_info
    format which details the files that are yet to be processed.
    :param s3:
    :param old_info: s3 location of the last job run info
    :param cdc_paths: the cdc paths being bookmarked
    :return:
    """
    if not cdc_paths:
        raise ValueError("cdc_paths cannot be null. It must be specified")
    if old_info:
        old_bucket, old_prefix = get_bucket_key(old_info)
        s3.download_file(old_bucket, old_prefix, 'old_info.json')
        old_file = open("old_info.json", "r")
        old = json.loads(old_file.read())
        old_file.close()
        since = old['max_ts']
        old_processed = old['files']
        new_run_id = old['run_id'] + 1
    else:
        # Assumes that there are no previous runs/no previously processed files
        old_processed = []
        since = '1970-01-01 00:00:00.000'
        new_run_id = 0

    unprocessed = []
    for path in cdc_paths:
        current = s3_list(s3, path, ListType.full)
        unprocessed.extend(current)

    new_files, new_max_ts = find_latest(old_processed, unprocessed, since)

    output = {
        'max_ts': new_max_ts.strftime('%Y-%m-%d %H:%M:%S.%f'),
        'files': new_files,
        'complete': False,
        'run_id': new_run_id

    }
    return output
