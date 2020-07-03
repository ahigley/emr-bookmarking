import zipfile
import os


def zipdir(path, zipf):
    for root, dirs, files in os.walk(path):
        for file in files:
            zipf.write(os.path.join(root, file))


zf = zipfile.ZipFile('package.zip', 'w', zipfile.ZIP_DEFLATED)
zf.write('../spark_jobs/sample_job/sample_job.py', 'sample_job.py')
zf.write('../spark_jobs/sample_job/requirements.txt', 'requirements.txt')
zipdir('../bookmarking/', zf)
zf.close()