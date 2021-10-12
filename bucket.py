import boto3
import boto3.session


class Bucket:
    def __init__(self):
        self.session = session = boto3.session.Session(
            aws_access_key_id='',
            aws_secret_access_key='',
            aws_session_token=''
        )
        self.s3 = session.resource('s3')
    
    def list_buckets(self):
        return self.s3.buckets.all()
