import argparse
from collections import defaultdict
import sys

import controller


DATE_FORMAT = '%Y-%m-%dT%H:%M'


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


# todo: argument size_unit should ignore case
class S3Cli:
    """CLI to display S3 buckets stats"""
    col_widths = (22, 7, 10, 7, 17, 17)
    parser = argparse.ArgumentParser('Display AWS S3 Buckets Information')
    parser.add_argument('--size-unit', default=SIZE_UNITS.KB, choices=SIZE_UNITS.choices,
                        help='Unit to display file size in.')
    parser.add_argument('--group-by', default=None, choices=('region'),
                        help='Attribute to group buckets by.')
    s3_controller = controller.S3()

    class GROUP:
        """Enum for grouping choices"""
        REGION = 'region'

        @staticmethod
        def get_region(bucket_name):
            return S3Cli.s3_controller.get_region(bucket_name)

        @classmethod
        def get(cls, group_key):
            return cls.funcs[group_key]

    GROUP.funcs = {
        GROUP.REGION: GROUP.get_region
    }

    def __init__(self):
        self.size_unit = SIZE_UNITS.KB

    @property
    def headers(self):
        return ['BUCKET', 'COUNT', f'SIZE ({self.size_unit})', 'COST', 'CREATION DATE', 'LAST CHANGE']

    def run(self):
        """Entry-point to launch everything"""
        args = self.parser.parse_args()
        self.size_unit = args.size_unit
        self.group_by = self.GROUP.get(args.group_by) if args.group_by is not None else None
        if self.group_by is None:
            self.display_buckets()
        else:
            self.display_by_region()

    def get_bucket_info(self, bucket):
        creation_date = bucket.creation_date.strftime(DATE_FORMAT)
        last_modified = None
        count = 0
        size = 0
        cost = 0
        for last in bucket.objects.all():
            # print('storage_class', last.storage_class)
            count += 1
            size += last.size
            cost += self.s3_controller.compute_cost(last)
            last_modified = max(last_modified, last.last_modified) if last_modified is not None else last.last_modified
        return controller.BucketInfo(bucket.name, count, size, cost, creation_date, last_modified)

    def display_buckets(self):
        bucket = None
        self._display_row(self.headers)
        for bucket in self.s3_controller.list_buckets():
            info = self.get_bucket_info(bucket)
            info.last_modified = info.last_modified.strftime(DATE_FORMAT) if info.last_modified is not None else ''
            info.size = convert_size_to(info.size, self.size_unit)
            info.cost = round(info.cost / 1e5, 2)
            self._display_row(info.as_list())

        if bucket is None:
            print('Aucun bucket à afficher.')

    def display_by_region(self):
        self._display_row(self.headers)

        groups = defaultdict(controller.BucketInfo)
        for bucket in self.s3_controller.list_buckets():
            info = self.get_bucket_info(bucket)
            region = self.group_by(info.name)
            groups[region].count += info.count
            groups[region].size += info.size
            groups[region].cost += info.cost
            groups[region].last_modified = max(groups[region].last_modified, info.last_modified)
        for name, group in groups.items():
            group.name = name
            group.last_modified = group.last_modified.strftime(DATE_FORMAT)
            group.size = convert_size_to(group.size, self.size_unit)
            group.cost = round(group.cost / 1e5, 2)
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
