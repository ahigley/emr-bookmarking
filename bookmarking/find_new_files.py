import boto3
import datetime
import pytz
import typing
from bookmarking.utilities import get_bucket_prefix
# https://stackoverflow.com/questions/2514961/remove-all-values-within-one-list-from-another-list
# This is the fastest way
def remove_common(first: list, second: list):
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


# def get_old_new(s3, old_info: typing.Optional[str] = None, cdc_paths: typing.Optional[str] = None):
#     """
#     Gets the list of objects of old and new and compares them. Returns a file that conforms to the old_info
#     format which details the files that are yet to be processed.
#     :param s3:
#     :param old_info:
#     :param cdc_paths:
#     :return:
#     """
#     if not old_info or cdc_paths:
#         raise ValueError("Both old_path and cdc_paths cannot be null. At least one must be specified")
#     old_bucket, old_prefix = get_bucket_prefix(old_info)
#
#     s3.