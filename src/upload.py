import hashlib
import sys
from pathlib import Path

from common import BUCKET, CSV_KEY, s3_client

path = Path(sys.argv[1])
s3 = s3_client()

try:
    s3.head_bucket(Bucket=BUCKET)
except s3.exceptions.ClientError as exc:
    if exc.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
        raise
    s3.create_bucket(Bucket=BUCKET)

digest = hashlib.md5()
with path.open("rb") as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(block)

print(f"local size={path.stat().st_size} md5={digest.hexdigest()}", flush=True)
s3.upload_file(str(path), BUCKET, CSV_KEY)

remote = hashlib.md5()
body = s3.get_object(Bucket=BUCKET, Key=CSV_KEY)["Body"]
while block := body.read(8 * 1024 * 1024):
    remote.update(block)

size = s3.head_object(Bucket=BUCKET, Key=CSV_KEY)["ContentLength"]
print(f"s3 size={size} md5={remote.hexdigest()}", flush=True)

if remote.digest() != digest.digest():
    raise SystemExit("MD5 mismatch")
print("MD5 matches", flush=True)
