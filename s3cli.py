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


# todo: argument size_unit should ignore case
class S3Cli:
    col_widths = (22, 7, 10, 7, 17, 17)
    parser = argparse.ArgumentParser('Client d\'analyse pour AWS S3')
    parser.add_argument('--size-unit', default=SIZE_UNITS.KB, choices=SIZE_UNITS.choices)
    s3_controller = bucket.Bucket()

    def __init__(self):
        self.size_unit = SIZE_UNITS.KB

    @property
    def headers(self):
        return ['BUCKET', 'COUNT', f'SIZE ({self.size_unit})', 'COST', 'CREATION DATE', 'LAST CHANGE']

    def run(self):
        args = self.parser.parse_args()
        self.size_unit = args.size_unit
        self.display_buckets()
    
    def display_buckets(self):
        bucket = None
        self._display_row(self.headers)
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
            self._display_row([bucket.name, str(count), str(size), str(round(cost / 1e5, 2)), creation_date, last_modified])

        if bucket is None:
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
