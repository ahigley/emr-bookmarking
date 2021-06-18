import unittest
from moto import mock_lambda
import boto3
from legacy.emr_resolver.resolve_job import update_lambda

@mock_lambda
class TestUpdateLambda(unittest.TestCase):

    def setUp(self) -> None:
        aws_lambda = boto3.client('lambda')
        aws_lambda.create_function(
            FunctionName='test_lambda',
            Runtime='python3.7',
            Role='arn:aws:iam::22222222222:role/test_lambda_role',
            Handler='test.lambda_hander',
            Code={
                'ZipFile': b'bytes',
                'S3Bucket': 'string',
                'S3Key': 'string',
                'S3ObjectVersion': 'string'
            },
            Timeout=123,
            MemorySize=128,
            Environment={
                'Variables': {
                    'do_not_change': 'not_changed',
                    'last_run': 'hopefully_changed'
                }
            },
        )

    def tearDown(self) -> None:
        aws_lambda = boto3.client('lambda')
        aws_lambda.delete_function(
            FunctionName='test_lambda'
        )

    # Tests that the environment variable desired is changed, and only the desired environment variable
    def test_update_lambda(self):
        name = 'test_lambda'
        last_run = 'some_last_run'
        expected_do_not_change = 'not_changed'
        aws_lambda = boto3.client('lambda')
        update_lambda(aws_lambda, name, last_run)
        response = aws_lambda.get_function(
            FunctionName=name
        )
        environment_vars = response['Configuration']['Environment']['Variables']
        self.assertEqual(environment_vars['last_run'], last_run)
        self.assertEqual(environment_vars['do_not_change'], expected_do_not_change)
