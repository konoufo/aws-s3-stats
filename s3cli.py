import argparse
from collections import defaultdict
from collections import OrderedDict
import sys

import controller
import settings


DATE_FORMAT = settings.DATE_FORMAT


class SIZE_UNITS:
    B = 'B'
    KB = 'KB'
    MB = 'MB'
    GB = 'GB'

    units = {
        B: 1,
        KB: 1024,
        MB: 1024 ** 2,
        GB: 1024 ** 3,
    }

    choices = units.keys()

    @classmethod
    def compute_bytes(cls, unit):
        return cls.units[unit]


def convert_size_to(size_in_bytes, size_unit, precision=2):
    return round(size_in_bytes / SIZE_UNITS.compute_bytes(size_unit), precision)


def bucket_info_format(info, size_unit=SIZE_UNITS.KB):
    storage_labels = {
        controller.Pricing.STANDARD: 'S',
        controller.Pricing.STANDARD_IA: 'IA',
        controller.Pricing.REDUCED_REDUNDANCY: 'RR'
    }
    info.last_modified = info.last_modified.strftime(DATE_FORMAT)
    info.creation_date = info.creation_date.strftime(DATE_FORMAT)
    info.size = convert_size_to(info.size, size_unit)
    info.cost = round(info.cost / 1e5, 2)
    info.storage_count = ','.join(f'{label}:{info.storage_count[s]}' for (s, label) in storage_labels.items())
    return info


# todo: argument size_unit should ignore case
class S3Cli:
    """CLI to display S3 buckets stats"""
    col_widths = (22, 7, 10, 7, 17, 17, 24)
    parser = argparse.ArgumentParser('Display Your AWS S3 Buckets Statistics.')
    parser.add_argument('--size-unit', default=SIZE_UNITS.KB, choices=SIZE_UNITS.choices,
                        help='Size unit to display file size in.')
    parser.add_argument('--group-by', default=None, choices=('region',),
                        help='Group buckets by a given attribute.')
    parser.add_argument('--bucket-name', default=None, help='Show bucket with given name.')
    parser.add_argument('--object-prefix', default='', help='Filter objects to be included in  by key prefix.')

    class GROUPFactory:
        """Enum for grouping choices"""
        REGION = 'region'

        def __init__(self, funcs):
            self.funcs = funcs

        def get(self, group_key):
            return self.funcs[group_key]

    def __init__(self, s3_controller=None):
        self.s3_controller = s3_controller or controller.S3()
        self.size_unit = SIZE_UNITS.KB
        self.get_bucket_objects = self.s3_controller.get_bucket_objects
        self.get_group_key = None
        self.bucket_filters = {}
        self.object_filters = {}
        self.GROUP = self.GROUPFactory({
            self.GROUPFactory.REGION: self.s3_controller.get_region
        })

    @property
    def headers(self):
        return ['BUCKET', 'COUNT', f'SIZE ({self.size_unit})', 'COST', 'CREATION DATE', 'LAST CHANGE', 'STORAGE CLASSES']

    def run(self):
        """Entry-point to launch everything"""
        self.parse_args()
        self._display_row(self.headers)
        if self.get_group_key is None:
            self.display_buckets()
        else:
            self.display_by_region()

    def parse_args(self):
        args = self.parser.parse_args()
        self.size_unit = args.size_unit
        self.get_group_key = self.GROUP.get(args.group_by) if args.group_by is not None else None
        self.get_bucket_objects = self.s3_controller.get_bucket_objects
        self.bucket_filters['name'] = args.bucket_name
        self.object_filters['Prefix'] = args.object_prefix

    def display_buckets(self):
        bucket = None
        for bucket in self.s3_controller.list_buckets(**self.bucket_filters):
            info = self.s3_controller.get_bucket_info(bucket, **self.object_filters)
            info = bucket_info_format(info, size_unit=self.size_unit)
            self._display_row(info.as_list())

        if bucket is None:
            print('Aucun bucket à afficher.')

    def display_by_region(self):
        assert self.get_group_key is not None, 'run() must be called first.'

        groups = defaultdict(controller.BucketInfo)
        for bucket in self.s3_controller.list_buckets(**self.bucket_filters):
            info = self.s3_controller.get_bucket_info(bucket)
            region = self.get_group_key(info.name)
            groups[region].count += info.count
            groups[region].size += info.size
            groups[region].cost += info.cost
            for s in info.storage_count:
                groups[region].storage_count[s] += info.storage_count[s]
            groups[region].last_modified = max(groups[region].last_modified, info.last_modified)
            groups[region].creation_date = min(groups[region].creation_date, info.creation_date)
        for name, group in groups.items():
            group.name = name
            group = bucket_info_format(group, size_unit=self.size_unit)
            self._display_row(group.as_list())

        if not len(groups.keys()):
            print('Aucun bucket à afficher.')

    def _display_row(self, info_list):
        assert len(info_list) == len(self.col_widths), f'Incorrect number of items in row: {info_list}'
        row_format = ' '.join(f'{{:<{w}}}' for w in self.col_widths)
        print(
            row_format.format(*(info if len(info) <= width else f'{info[:width - 3]}...'
                                    for (info, width) in zip(info_list, self.col_widths)))
        )


if __name__ == '__main__':
    S3Cli().run()
