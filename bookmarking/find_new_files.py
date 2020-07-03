import datetime
import pytz
import typing
import json
import os
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
    return remove_common(filtered_new, old), max_date.strftime('%Y-%m-%d %H:%M:%S.%f')


def get_old_new(s3, cdc_prefixes: typing.Optional[list] = None, full_load_prefixes: typing.Optional[list] = None,
                old_info: typing.Optional[str] = None):
    """
    Gets the list of objects of old and new and compares them. Returns a dictionary that conforms to the old_info
    format which details the files that are yet to be processed.
    :param s3:
    :param old_info: s3 location of the last job run info
    :param cdc_prefixes: list of cdc prefixes
    :param full_load_prefixes: list of full_load prefixes
    :return:
    """
    if not cdc_prefixes and full_load_prefixes:
        raise ValueError("cdc_info and full_load_info cannot both be null. One must be specified")

    if old_info:
        old_bucket, old_prefix = get_bucket_key(old_info)
        s3.download_file(old_bucket, old_prefix, 'old_info.json')
        old_file = open("old_info.json", "r")
        old = json.loads(old_file.read())
        old_file.close()
        os.remove('old_info.json')
        new_run_id = old['run_id'] + 1
    else:
        # Assumes that there are no previous runs/no previously processed files
        old = {'cdc_files': {}}
        new_run_id = 0

    if cdc_prefixes:
        new_cdc = {}
        # Add any newly added identifiers, update previous prefixes, drop missing ones
        for prefix in cdc_prefixes:
            old_cdc = old['cdc_files']
            old_files = old_cdc.get(prefix, {}).get('files', [])
            since = old_cdc.get(prefix, {}).get('max_ts', "1970-01-01 00:00:00.000")
            files, max_ts = find_latest(old_files, s3_list(s3, prefix, ListType.full), since)
            new_cdc[prefix] = {'files': files, 'max_ts': max_ts}
    else:
        new_cdc = None

    if full_load_prefixes:
        new_full = {}
        for prefix in full_load_prefixes:
            files = s3_list(s3, prefix, ListType.full)
            new_full[prefix] = {'files': [x[0] for x in files]}
    else:
        new_full = None

    output = {
        'cdc_files': new_cdc,
        'full_load_files': new_full,
        'complete': False,
        'run_id': new_run_id
    }
    return output
