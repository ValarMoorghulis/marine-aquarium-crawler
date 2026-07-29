"""海水水族智能爬虫 - 主入口"""
import argparse
import sys
from pathlib import Path

from crawler.engine import CrawlerEngine
from trust.evaluator import TrustEvaluator
from storage.sqlite_store import SQLiteStore
from storage.git_sync import GitSyncer


def main():
    parser = argparse.ArgumentParser(description="Marine Aquarium Crawler")
    parser.add_argument("--mode", choices=["full", "incremental", "evaluate", "sync", "status"],
                        default="incremental", help="运行模式")
    parser.add_argument("--source", type=str, help="指定单个源ID")
    parser.add_argument("--input", type=str, help="输入目录（evaluate模式用）")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不写入")
    args = parser.parse_args()

    store = SQLiteStore("data/crawler.db")

    if args.mode in ("full", "incremental"):
        engine = CrawlerEngine(store=store, source_id=args.source)
        if args.mode == "full":
            engine.crawl_all()
        else:
            engine.crawl_incremental()

    elif args.mode == "evaluate":
        evaluator = TrustEvaluator()
        input_dir = Path(args.input or "data/raw")
        evaluator.evaluate_directory(input_dir)

    elif args.mode == "sync":
        syncer = GitSyncer(store=store)
        syncer.sync_to_vault()

    elif args.mode == "status":
        store.print_stats()


if __name__ == "__main__":
    main()
