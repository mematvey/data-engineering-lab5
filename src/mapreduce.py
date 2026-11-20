import csv
import io

from common import BUCKET, CSV_KEY

OVERLAP = 1 << 20


def read_header(s3):
    body = s3.get_object(
        Bucket=BUCKET,
        Key=CSV_KEY,
        Range="bytes=0-65535",
    )["Body"].read()

    line = body.split(b"\n")[0].decode("utf-8").rstrip("\r")
    columns = next(csv.reader([line]))

    return {
        "role": columns.index("role"),
        "name": columns.index("name"),
        "skills": columns.index("key_skills"),
    }


def split_chunks(size, chunk_bytes):
    chunks = []
    start = 0

    while start < size:
        end = min(start + chunk_bytes, size)
        chunks.append((len(chunks), start, end))
        start = end

    return chunks


def read_lines(s3, size, start, end):
    first = max(start - 1, 0)
    last = min(end + OVERLAP, size)
    body = s3.get_object(
        Bucket=BUCKET,
        Key=CSV_KEY,
        Range=f"bytes={first}-{last - 1}",
    )["Body"].read()

    position = first
    if start > 0:
        cut = body.find(b"\n") + 1
        body = body[cut:]
        position += cut

    lines = []
    parts = body.split(b"\n")

    for index, part in enumerate(parts):
        if position >= end:
            break
        if index == len(parts) - 1 and last < size:
            raise RuntimeError("строка длиннее запаса OVERLAP, увеличь его")

        position += len(part) + 1
        if part:
            lines.append(part.rstrip(b"\r").decode("utf-8"))

    return lines


def to_csv_bytes(counter):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["skills", "count"])

    for skills, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        writer.writerow([" | ".join(skills), count])

    return output.getvalue().encode("utf-8")
