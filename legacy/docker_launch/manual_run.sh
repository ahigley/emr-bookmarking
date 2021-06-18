#!/usr/bin/env bash

aws ecs run-task --cluster emr-bookmarking-cluster --launch-type FARGATE --task-definition launcher:2 --network-configuration 'awsvpcConfiguration={subnets=[subnet-0073ff41613d4d21e,subnet-026710de496bff2bc],assignPublicIp=ENABLED}' --overrides file://overrides.json
