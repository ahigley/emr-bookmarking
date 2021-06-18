#!/bin/bash

export PYSPARK_PYTHON="/usr/bin/python3"

/usr/bin/spark-submit --master yarn-client $HOME/{job_script} {arguments}
