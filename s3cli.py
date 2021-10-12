import argparse

import bucket


DATE_FORMAT = '%Y-%m-%dT%H:%M'


class SIZE_UNITS:
    KB = 1024
    MB = 1024 ** 2
    GB = 1024 ** 3


def convert_size_to(size_in_octets, size_unit):
    return round(size_in_octets / size_unit, 2)


class S3Cli:
    parser = argparse.ArgumentParser('Client d\'analyse pour AWS S3')
    s3_controller = bucket.Bucket()

    def run(self, args_list=None):
        args = self.parser.parse_args([] if args_list is None else args_list)
        self.display_buckets()
    
    def display_buckets(self):
        for i in self.s3_controller.list():
            creation_date = i.creation_date.strftime(DATE_FORMAT)
            last_modified = None
            count = 0
            size = 0
            for last in bucket.objects.all():
                print('storage_class', last.storage_class)
                count += 1
                size += last.size
                last_modified = min(last_modified, last.last_modified) if last_modified is not None else last.last_modified
            if last_modified is not None:
                last_modified = last_modified.strftime(DATE_FORMAT)
            size = convert_size_to(size, SIZE_UNITS.KB)
            print([bucket.name, count, size, creation_date, last_modified])
        if bucket is None:
            print('Aucun bucket à afficher.')


if __name__ == '__main__':
    S3Cli().run()
