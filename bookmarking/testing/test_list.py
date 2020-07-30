import unittest
import boto3
from moto import mock_s3
import datetime
import pytz


from bookmarking.s3_list import s3_list, ListType
BUCKET = 'mock-test-bucket'
local_files = ['test_files/test_a.txt', 'test_files/test_b.txt']


@mock_s3
class TestListS3FilesFull(unittest.TestCase):
    before_upload = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

    def setUp(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        s3_client.create_bucket(
            ACL='private',
            Bucket=BUCKET
        )
        for x in range(0, 2000):
            s3_client.upload_file(local_files[0], BUCKET, local_files[0].replace('a', str(x)))
            s3_client.upload_file(local_files[0], BUCKET, F"subprefix1/subprefix2/{local_files[1].replace('b', str(x))}")


    def tearDown(self) -> None:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id="fake",
            aws_secret_access_key="fake_secret"
        )
        for x in range(0, 2000):
            s3_client.delete_object(
                Bucket=BUCKET,
                Key=local_files[0].replace('a', str(x))
            )
            s3_client.delete_object(
                Bucket=BUCKET,
                Key=F"subprefix1/subprefix2/{local_files[1].replace('b', str(x))}"
            )

        s3_client.delete_bucket(
            Bucket=BUCKET
        )

    def test_list_full(self) -> None:
        s3_client = boto3.client('s3')
        paths = s3_list(s3_client, F"s3://{BUCKET}/", how=ListType.full)
        self.assertTrue(isinstance(paths, list))
        self.assertEqual(len(paths), 4000)
        expected_paths = [F"s3://{BUCKET}/{local_files[0].replace('a', str(x))}" for x in range(0, 2000)]
        expected_paths.extend([F"s3://{BUCKET}/subprefix1/subprefix2/"
                               F"{local_files[1].replace('b', str(x))}" for x in range(0, 2000)])
        self.assertCountEqual(paths, expected_paths)

    def test_list_prefix(self) -> None:
        s3_client = boto3.client('s3')
        paths = s3_list(s3_client, F"s3://{BUCKET}/", how=ListType.prefix)
        self.assertTrue(isinstance(paths, list))
        self.assertEqual(len(paths), 4000)
        expected_paths = [local_files[0].replace('a', str(x)) for x in range(0, 2000)]
        expected_paths.extend([F"subprefix1/subprefix2/"
                               F"{local_files[1].replace('b', str(x))}" for x in range(0, 2000)])
        self.assertCountEqual(paths, expected_paths)

    def test_list_object_only(self) -> None:
        s3_client = boto3.client('s3')
        paths = s3_list(s3_client, F"s3://{BUCKET}/", how=ListType.object_only)
        self.assertTrue(isinstance(paths, list))
        self.assertEqual(len(paths), 4000)
        expected_paths = [local_files[0].replace('a', str(x)).split('/')[-1] for x in range(0, 2000)]
        expected_paths.extend([local_files[1].replace('b', str(x)).split('/')[-1] for x in range(0, 2000)])
        self.assertCountEqual(paths, expected_paths)


if __name__ == "__main__":
    unittest.main()
