#!/bin/bash -x

aws s3 cp s3://{bucket}/{prefix} $HOME/
unzip -o $HOME/{package} -d $HOME

sudo pip-3.7 install -r $HOME/requirements.txt