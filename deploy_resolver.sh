#!/usr/bin/env bash
export ACCOUNT="021110012899"
# Log in command
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 021110012899.dkr.ecr.us-east-1.amazonaws.com
# Dockerfile requires files from bookmarking, but to get those files the command must be run from the parent directory
docker build -t sample_job-emr-resolver -f emr_resolver/Dockerfile .
docker tag sample_job-emr-resolver:latest "$ACCOUNT".dkr.ecr.us-east-1.amazonaws.com/sample_job-emr-resolver:latest
docker push "$ACCOUNT".dkr.ecr.us-east-1.amazonaws.com/sample_job-emr-resolver:latest