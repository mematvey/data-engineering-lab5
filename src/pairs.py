import argparse
import csv
import json
import os
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

from common import BUCKET, CSV_KEY, is_variant, parse_skills, s3_client
from mapreduce import read_header, read_lines, split_chunks, to_csv_bytes

csv.field_size_limit(10**8)


def worker(index, count):
    started = time.monotonic()
    s3 = s3_client()
    size = s3.head_object(Bucket=BUCKET, Key=CSV_KEY)["ContentLength"]
    columns = read_header(s3)
    result = Counter()

    chunks = split_chunks(size, 16 * 1024 * 1024)
    selected = [chunk for chunk in chunks if chunk[0] % count == index]

    for chunk_id, start, end in selected:
        lines = read_lines(s3, size, start, end)
        if start == 0:
            lines = lines[1:]

        for row in csv.reader(lines):
            if is_variant(row[columns["role"]], row[columns["name"]]):
                skills = parse_skills(row[columns["skills"]])
                result.update(combinations(skills, 2))

        print(f"part={index} chunk={chunk_id} pairs={len(result)}", flush=True)

    body = json.dumps(
        [[list(skills), count] for skills, count in result.items()],
        ensure_ascii=False,
    ).encode()
    key = f"results/k8s/parts/{index}.json"
    s3.put_object(Bucket=BUCKET, Key=key, Body=body)
    print(f"saved={key} chunks={len(selected)}", flush=True)

    peak = Path("/sys/fs/cgroup/memory.peak")
    if peak.exists():
        elapsed = time.monotonic() - started
        print(
            f"elapsed_seconds={elapsed:.3f} memory_peak_bytes={peak.read_text().strip()}",
            flush=True,
        )


def reduce_parts(count):
    s3 = s3_client()
    result = Counter()

    for index in range(count):
        key = f"results/k8s/parts/{index}.json"
        body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        result.update({tuple(skills): count for skills, count in json.loads(body)})

    data = to_csv_bytes(result)
    s3.put_object(Bucket=BUCKET, Key="results/k8s/stack_2.csv", Body=data)
    print("\n".join(data.decode().splitlines()[:11]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["worker", "reduce"])
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument(
        "--index",
        type=int,
        default=int(os.environ.get("JOB_COMPLETION_INDEX", "0")),
    )
    args = parser.parse_args()

    if args.mode == "worker":
        worker(args.index, args.count)
    else:
        reduce_parts(args.count)
