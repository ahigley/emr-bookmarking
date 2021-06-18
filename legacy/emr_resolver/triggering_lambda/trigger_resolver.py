import boto3
import os


def lambda_handler(event, context):
    ecs = boto3.client('ecs')
    cluster = os.environ['cluster']
    subnets_env = os.environ['subnets']
    subnets = subnets_env.split(',')
    resolver = os.environ['resolver']
    run_info = os.environ['run_info']
    temp_prefix = os.environ['temp_prefix']
    final_prefix = os.environ['final_prefix']
    meta_data_prefix = os.environ['meta_data_prefix']
    launcher_function = os.environ['launcher_function']
    ecs.run_task(
        cluster=cluster,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': subnets,
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': resolver,

                    'environment': [
                        {
                            'name': 'TEMP_PATH',
                            'value': temp_prefix
                        },
                        {
                            'name': 'FINAL_PATH',
                            'value': final_prefix
                        },
                        {
                            'name': 'META_DATA_PATH',
                            'value': meta_data_prefix
                        },
                        {
                            'name': 'RUN_INFO_PATH',
                            'value': run_info
                        },
                        {
                            'name': 'LAMBDA',
                            'value': launcher_function
                        }
                    ],
                },
            ],
        },
        taskDefinition=resolver
    )
