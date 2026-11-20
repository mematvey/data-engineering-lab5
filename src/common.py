import os
import re

import boto3
from botocore.config import Config

ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:9100")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "mematvey")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "mematvey-secret-123")
BUCKET = "hh-lake"
CSV_KEY = "raw/it_vacancies_2024.csv"

ROLES = ("Программист, разработчик", "Руководитель группы разработки")
NAME_PATTERN = re.compile(
    r"android|андроид|(^|[^a-z])ios([^a-z]|$)|swift|kotlin|flutter|react.native"
    r"|objective-c|xamarin|ionic|mobile|мобильн"
)


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(
            retries={"max_attempts": 3},
            connect_timeout=10,
            read_timeout=120,
        ),
    )


def is_variant(role, name):
    return role in ROLES and NAME_PATTERN.search(name.lower()) is not None


def parse_skills(raw):
    if not raw:
        return []

    return sorted({skill.strip().lower() for skill in raw.split("; ") if skill.strip()})
