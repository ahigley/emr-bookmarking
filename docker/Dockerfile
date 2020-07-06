FROM python:3.7
ADD bookmarking /bookmarking
ADD emr_launcher/requirements.txt /
ADD emr_launcher/launch_job.py /
RUN pip3 install -r ./requirements.txt
RUN pip3 install -r ./bookmarking/requirements.txt
CMD [ "python", "./launch_job.py"]