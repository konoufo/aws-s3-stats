# AWS S3 Analyzer CLI

## Installation

Retrieve source from repository:
```bash
git clone git@github.com:konoufo/aws-s3-stats.git
```
From root directory, install python packages:
```bash
pip install -r requirements.txt
```

## Usage
Make sure your AWS credentials are set up in your environment as usual. If you use `awscli`, you should be alright without further configuration.

Let's assume the following bucket structure:
```
appbucket/
├─ bar/
│ ├─ robots.txt
├─ index.html
foobucket/
├─ bar/
│ ├─ star.txt
├─ victor.jpg
```

To get information from all buckets:
```bash
python s3cli.py
```

To get information from a specific bucket named `foobucket`:
```bash
python s3cli.py --bucket-name foobucket
```

To include information only from objects with a given key prefix `bar`:
```bash
python s3cli.py --object-prefix bar
```

To group bucket information by region:
```bash
python s3cli.py --group-by region
```

## Development
Feel free to play around and contribute new code by creating a pull request.
A minimal test suite is included that should be tested against new changes:
```bash
python -m unittest tests.py
```
Also, feel free to contribute new tests.
