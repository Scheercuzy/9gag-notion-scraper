import argparse
from pydantic import BaseModel


class Arguments(BaseModel):
    skip_existing: bool
    stop_existing: bool


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="9gag-notion-scraper")
    parser.add_argument("--skip-existing", action='store_true')
    parser.add_argument("--stop-existing", action='store_true')
    return parser


def get_args() -> Arguments:
    # return _build_parser().parse_args()
    args = _build_parser().parse_args()
    return Arguments(
        skip_existing=args.skip_existing,
        stop_existing=args.stop_existing
    )
