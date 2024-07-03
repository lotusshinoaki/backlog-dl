# coding: utf_8
import os
from argparse import ArgumentParser
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .client import Client
from .list_shared_files import SizeFormatter, list_shared_files


class Args(BaseModel):
    PROJECT_ID: str
    exclude: str | None
    first: str | None
    human_readable: bool
    include: str | None
    last: str | None
    output: str
    root: str
    wait: float

    model_config = ConfigDict(from_attributes=True)


def install(subparsers) -> None:
    parser: ArgumentParser = subparsers.add_parser("download-shared-files")
    parser.add_argument(
        "-r",
        "--root",
        default="/",
        help="操作対象のルートディレクトリ",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=os.getcwd(),
        help="ダウンロード先のディレクトリ. デフォルトではカレントディレクトリ",
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


def _main(args_) -> None:
    args = Args.model_validate(args_)

    api_key = os.environ["BACKLOG_API_KEY"]
    domain = os.environ["BACKLOG_DOMAIN"]

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

            data = client.download_file(file.id)

            output_file = Path(args.output + file.path())
            if not output_file.parent.exists():
                output_file.parent.mkdir(parents=True, exist_ok=True)

            output_file.write_bytes(data)
