import asyncio
import sys
from datetime import datetime

from constants import REPORTS_RANGE, REPORTS_DIR
from import_to_db import create_model_and_import_data_to_db
from parser_stdlib import Parser, remove_reports_directory

from tqdm.asyncio import tqdm_asyncio


async def entrypoint() -> None:
    """
    Main entrypoint to parser application.

    Does all the things required to parse, process and upload data.
    """
    start = datetime.now()
    parser = Parser(site="https://spimex.com")
    fetch_tasks = [
        parser.fetch_and_parse_data(page_num) for page_num in REPORTS_RANGE
    ]
    result = await tqdm_asyncio.gather(
        *fetch_tasks, desc="Fetching data...", colour="green"
    )

    await tqdm_asyncio.gather(
        *[
            parser.collect_reports(url, f"report_{url.split('/')[-1]}")
            for page in result
            for url in page
        ],
        desc="Downloading reports...",
        colour="green",
    )
    await create_model_and_import_data_to_db()
    remove_reports_directory(REPORTS_DIR)
    end = datetime.now()
    sys.stdout.write(f"Total time elapsed: {(end - start).total_seconds()}")


if __name__ == "__main__":
    asyncio.run(entrypoint())
