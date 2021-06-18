import boto3
import os


def lambda_handler(event, context):
    ecs = boto3.client('ecs')
    cluster = os.environ['cluster']
    subnets_env = os.environ['subnets']
    subnets = subnets_env.split(',')
    inputs = os.environ['inputs']
    launcher = os.environ['launcher']
    last_run = os.environ['last_run']
    print(f"Starting ecs task with inputs = {inputs} last_run = {last_run}")
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
                    'name': launcher,

                    'environment': [
                        {
                            'name': 'INPUTS',
                            'value': inputs
                        },
                        {
                            'name': 'LAST_RUN',
                            'value': last_run
                        }
                    ],
                },
            ],
        },
        taskDefinition=launcher
    )
