#!/usr/bin/env bash
export ACCOUNT="021110012899"
# Log in command
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 021110012899.dkr.ecr.us-east-1.amazonaws.com
# Dockerfile requires files from bookmarking, but to get those files the command must be run from the parent directory
docker build -t emr-launcher -f docker/Dockerfile .
docker tag emr-launcher:latest "$ACCOUNT".dkr.ecr.us-east-1.amazonaws.com/emr-launcher:latest
docker push "$ACCOUNT".dkr.ecr.us-east-1.amazonaws.com/emr-launcher:latest