import argparse
import sys

import bucket


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


class S3Cli:
    parser = argparse.ArgumentParser('Client d\'analyse pour AWS S3')
    parser.add_argument('--size-unit', default=SIZE_UNITS.KB, choices=SIZE_UNITS.choices)
    s3_controller = bucket.Bucket()

    def run(self):
        args = self.parser.parse_args()
        self.size_unit = args.size_unit
        self.display_buckets()
    
    def display_buckets(self):
        bucket = None
        for bucket in self.s3_controller.list_buckets():
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
                last_modified = min(last_modified, last.last_modified) if last_modified is not None else last.last_modified
            if last_modified is not None:
                last_modified = last_modified.strftime(DATE_FORMAT)
            size = convert_size_to(size, self.size_unit)
            print('cost', cost)
            print([bucket.name, count, size, round(cost / 1e5, 2), creation_date, last_modified])
        if bucket is None:
            print('Aucun bucket à afficher.')


if __name__ == '__main__':
    S3Cli().run()
