# coding: utf_8
import argparse
import os
import sys

from . import download_shared_files, list_shared_files


def main() -> None:
    for k in ("BACKLOG_API_KEY", "BACKLOG_DOMAIN"):
        if k not in os.environ:
            print(f'環境変数"{k}"が設定されていません')
            sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.set_defaults(_main=None)

    subparsers = parser.add_subparsers()

    download_shared_files.install(subparsers)
    list_shared_files.install(subparsers)

    args = parser.parse_args()
    if args._main:
        args._main(args)
    else:
        parser.print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
