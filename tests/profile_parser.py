import sys
import cProfile
import io
import pstats

import efj_parser


def main():
    data = sys.stdin.read()
    parser = efj_parser.Parser()
    pr = cProfile.Profile()
    pr.enable()
    duties, sectors = parser.parse(data)
    pr.disable()
    s = io.StringIO()
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.dump_stats("/home/jon/downloads/profile")
    ps.print_stats()
    print(s.getvalue())
    print(f"{len(sectors)} sectors, {len(duties)} duties")


if __name__ == "__main__":
    main()
