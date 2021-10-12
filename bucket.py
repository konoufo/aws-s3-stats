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

    def compute_cost(self, object):
        """Return monthly storage cost for a given S3 object. Units are 1/100,000 US$"""
        return Pricing.compute_gigabyte_price(object.storage_class) * math.ceil(object.size / (1024 ** 3))
