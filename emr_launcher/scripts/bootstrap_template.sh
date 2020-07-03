#!/bin/bash

aws s3 cp s3://{bucket}/{prefix} $HOME/
unzip -o $HOME/{package} -d $HOME

sudo easy_install-3.4 pip
sudo /usr/local/bin/pip3 install -r $HOME/requirements.txt