import sys

import efj_parser
from time import time_ns as time


def main():
    data = sys.stdin.read()
    start = time()
    parser = efj_parser.Parser()
    duties, sectors = parser.parse(data)
    end = time()
    print(f"Parsed {len(sectors)} sectors, {len(duties)} duties "
          f"in {int((end - start) / 1e3)} microseconds")
    start = time()
    block_total = sum(map(lambda s: s.total, sectors))
    duty_total = sum(map(lambda d: d.duration, duties))
    end = time()
    print(f"Calculated {block_total} minutes of flight time and "
          f"{duty_total} minutes of duty time "
          f"in {int((end - start) / 1e3)} microseconds")


if __name__ == "__main__":
    main()
