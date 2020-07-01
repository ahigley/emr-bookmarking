#!/bin/bash

aws s3 cp s3://{bucket}/{prefix} $HOME/
unzip -o $HOME/{package} -d $HOME

export PYSPARK_PYTHON="/usr/bin/python3"

/usr/bin/spark-submit --master yarn-client $HOME/{job_script}.py {arguments}
