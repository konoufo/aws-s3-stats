import argparse
import bucket
import itertools


DATE_FORMAT = '%Y-%m-%dT%H:%M'


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
            for last in i.object_versions.filter():
                print(last)
                last_modified = last.last_modified
            last_modified = last_modified.strftime(DATE_FORMAT)
            print([i.name, len(list(i.objects.all())), creation_date, last_modified])
        else:
            print('Aucun bucket à afficher.')


if __name__ == '__main__':
    S3Cli().run()
