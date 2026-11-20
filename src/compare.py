import csv
import io
import sys
from pathlib import Path

from common import BUCKET, s3_client

with Path(sys.argv[1]).open(encoding="utf-8", newline="") as file:
    expected = list(csv.reader(file))

body = s3_client().get_object(Bucket=BUCKET, Key="results/k8s/stack_2.csv")["Body"]
data = body.read().decode("utf-8")
actual = list(csv.reader(io.StringIO(data, newline="")))

print(f"rows: hw3={len(expected) - 1} k8s={len(actual) - 1}")
print(f"top10 equal: {expected[:11] == actual[:11]}")
print(f"all rows equal: {expected == actual}")

if expected != actual:
    raise SystemExit(1)
