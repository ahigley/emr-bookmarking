FROM python:3.7
ADD bookmarking /bookmarking
ADD emr_resolver/requirements.txt /
ADD emr_resolver/resolve_job.py /
RUN pip3 install -r ./requirements.txt
RUN pip3 install -r ./bookmarking/requirements.txt
CMD [ "python", "./resolve_job.py"]