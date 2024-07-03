# coding: utf_8
import os
from argparse import ArgumentParser
from collections import defaultdict, deque
from fnmatch import fnmatch
from typing import Iterable, Self

from pydantic import BaseModel, ConfigDict

from .client import Client, SharedFile


class Args(BaseModel):
    PROJECT_ID: str
    exclude: str | None
    first: str | None
    human_readable: bool
    include: str | None
    last: str | None
    root: str
    wait: float

    model_config = ConfigDict(from_attributes=True)


class FileFilter:
    def __init__(
        self: "FileFilter",
        *,
        include: str | None,
        exclude: str | None,
        first: str | None,
        last: str | None,
    ) -> None:
        self._include = include
        self._exclude = exclude
        self._first = first
        self._last = last

    def match(self: Self, file: SharedFile) -> bool:
        return bool(
            (self._first and file.updated < self._first)
            or (self._last and file.updated > self._last)
            or (self._include and not fnmatch(file.name, self._include))
            or (self._exclude and fnmatch(file.name, self._exclude))
        )


class SizeFormatter:
    def __init__(
        self: "SizeFormatter",
        *,
        human_readable: bool,
    ) -> None:
        self._human_readable = human_readable

    def format(self: Self, value: int) -> str:
        if (not self._human_readable) or value < 1024:
            return str(value)
        elif value < 10240:
            return f"{value/1024:.1f}KB"
        elif value < 1048576:
            return f"{value//1024}KB"
        elif value < 10485760:
            return f"{value/1048576:.1f}MB"
        elif value < 1073741824:
            return f"{value//1048576}MB"
        else:
            return f"{value/1073741824:.1f}GB"


def install(subparsers) -> None:
    parser: ArgumentParser = subparsers.add_parser("list-shared-files")
    parser.add_argument(
        "-r",
        "--root",
        default="/",
        help="操作対象のルートディレクトリ",
    )
    parser.add_argument(
        "-i",
        "--include",
        help="操作対象に含まれるファイル名のパターン(glob)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="操作対象から除外するファイル名のパターン(glob)",
    )
    parser.add_argument(
        "-f",
        "--first",
        help="操作対象に含まれるファイル更新日の開始日(YYYY-MM-DD)",
    )
    parser.add_argument(
        "-l",
        "--last",
        help="操作対象に含まれるファイル更新日の終了日",
    )
    parser.add_argument(
        "-H",
        "--human-readable",
        action="store_true",
        help="単位(KB, MB, GB)を用いてファイルサイズを表示する",
    )
    parser.add_argument(
        "-w",
        "--wait",
        type=float,
        default=1.0,
        help="BacklogAPIへのリクエスト間隔(秒). 1秒以上が推奨されている",  # noqa
    )
    parser.add_argument("PROJECT_ID")
    parser.set_defaults(_main=_main)


def list_shared_files(
    *,
    client: Client,
    root: str,
    include: str | None,
    exclude: str | None,
    first: str | None,
    last: str | None,
) -> Iterable[SharedFile]:
    file_filter = FileFilter(
        include=include,
        exclude=exclude,
        first=first,
        last=last,
    )

    queue: deque[str] = deque()
    queue.append(root)

    while queue:
        path = queue.pop()
        for f in client.list_shared_files(path):
            if f.type == "directory":
                queue.append(f.path())
            elif file_filter.match(f):
                pass
            else:
                yield f


def _main(args_) -> None:
    args = Args.model_validate(args_)

    api_key = os.environ["BACKLOG_API_KEY"]
    domain = os.environ["BACKLOG_DOMAIN"]

    counter: defaultdict[str, int] = defaultdict(int)
    formatter = SizeFormatter(human_readable=args.human_readable)

    with Client(
        domain=domain,
        project_id=args.PROJECT_ID,
        api_key=api_key,
        wait=args.wait,
    ) as client:
        for file in list_shared_files(
            client=client,
            root=args.root,
            include=args.include,
            exclude=args.exclude,
            first=args.first,
            last=args.last,
        ):
            size = formatter.format(file.size_())
            print(f"{file.id}\t{size}\t{file.updated}\t{file.path()}")

            counter[file.dir] += file.size_()

    print()
    for d, s in counter.items():
        size = formatter.format(s)
        print(f"{d}\t{size}")
