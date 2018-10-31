"""
* The web application should allow authorized users to perform following operations:
    * Upload new files. (max size 10 MB per file) (Create)
    * Browse through already uploaded list of files with each record having a URL to download the fie. (Read/ List Page)
    * Update already uploaded files. (Update Page)
    * Delete already uploaded file (Delete Page)
* For each file upload, application should track following fields:
    * Users first name
    * Users last name
    * File Upload Time
    * File Updated Time
    * File Description
"""

import boto3

class BotoClient(object):
    """
    """
    def __init__(self, service_name, **creds):
        self.service_name = service_name
        self.creds = creds

    @property
    def client(self):
        client = boto3.client(self.service_name, **self.creds)
        return client

class S3Client(BotoClient):
    
    def __init__(self, **creds):
        super(S3Client, self).__init__("s3", **creds)

    def upload_data(self, local_path, bucket, s3_key):
        with open(local_path, 'rb') as data:
            print data, bucket, s3_key
            self.client.upload_fileobj(data, bucket, s3_key)

    def upload_file(self, data, bucket, s3_key):
        self.client.upload_fileobj(data, bucket, s3_key)

    def download_file(self, bucket, filename, dest):
        self.client.download_file(bucket, filename, dest_path)

    def download_data(self, s3_path, dest_path):
        bucket, key = s3_path.split("/", 1)
        self.client.download_file(bucket, key, dest_path)
    
    def get_object(self, bucket, filename):
        #import pdb; pdb.set_trace()
        return self.client.get_object(Bucket=bucket, Key=filename)

    def delete_object(self, bucket, key):
        self.client.delete_object(Bucket=bucket, Key=key)

    def list_all_objects(self, bucket, prefix=None):
        paginator = self.client.get_paginator('list_objects')
        #pages = paginator.paginate(Bucket=bucket)
        if(prefix):
            opParameters = {"Bucket":bucket, "Prefix":prefix}
            pages = paginator.paginate(**opParameters)
        else:
            pages = paginator.paginate(Bucket=bucket)
        for page in pages:

            for s3_obj in page['Contents']:
                yield s3_obj

if __name__ == '__main__':
    """ Self Test  """
    s3client = S3Client()
    for i in s3client.list_all_objects('wpmedia123', 'viswanath_f9c0f39a/'):
        print i
