from collections import OrderedDict
import datetime
from logging import warning
import math

import boto3
import boto3.session


class Pricing:
    """Pricing (/GB) per storage class. Prices are in thousandth of US$ cents e.g 2300 -> 0.023 US$"""
    standard50 = 'standard'
    standard450 = 'standard'
    standard500 = 'standard'
    standard_ia = 'standard-ia'
    onezone = 'one zone-ia'
    glacier = 'glacier'
    glacier_da = 'glacier deep archive'

    prices = {
        standard50: 2300,
        # standard450: 2200,
        # standard500: 2100,
        standard_ia: 1250,
        onezone: 1000,
        glacier: 400,
        glacier_da: 99
    }

    @classmethod
    def compute_gigabyte_price(cls, storage_class):
        """Return monthly GB price for a given storage class. Units are 1/100,000 US$"""
        try:
            return cls.prices[storage_class.lower()]
        except KeyError:
            warning(f'Unknown storage class: {storage_class}. (Default is: {cls.standard50})')
            return cls.prices[cls.standard50]


class S3:
    def __init__(self):
        self.session = session = boto3.session.Session(
            aws_access_key_id='',
            aws_secret_access_key='',
            aws_session_token=''
        )
        self.s3 = session.resource('s3')
    
    def list_buckets(self):
        return self.s3.buckets.all()

    def get_region(self, bucket_name):
        location = self.session.client('s3').get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        #print(location)
        return location or 'us-east-1'

    def compute_cost(self, object):
        """Return monthly storage cost for a given S3 object. Units are 1/100,000 US$"""
        return Pricing.compute_gigabyte_price(object.storage_class) * math.ceil(object.size / (1024 ** 3))


class BucketInfo:
    UTC = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc)
    def __init__(self, name=0, count=0, size=0, cost=0, creation_date=None, last_modified=UTC):
        self.infos = OrderedDict((
            ('name', name),
            ('count', count),
            ('size', size),
            ('cost', cost),
            ('creation_date', creation_date),
            ('last_modified', last_modified)
        ))

    def as_list(self):
        return [str(v) for v in self.infos.values()]

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            #print('attibuterror', name)
            pass
        try:
            # print(self.infos)
            return self.infos[name]
        except KeyError:
            raise KeyError(f'Key does not exist in data object: "{name}"')

    def __setattr__(self, name, value):
        if name == 'infos':
            return super().__setattr__(name, value)
        if name not in self.infos:
            raise KeyError(f'Key does not exist in data object: "{name}"')
        self.infos[name] = value
