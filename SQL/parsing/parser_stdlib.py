import asyncio
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
import os
import re
import logging
from typing import Optional
from urllib.request import urlopen, urlretrieve
import pathlib

import xlrd

BASE_DIR = pathlib.Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_RANGE = range(45, 0, -1)
CONTRACT_VALUE_IDX = -1
TABLE_ID_ROW_STARTING_AT = 8

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())


@dataclass(slots=True)
class Instrument:
    exchange_product_id: str
    exchange_product_name: str
    oil_id: str
    delivery_basis_id: str
    delivery_basis_name: str
    delivery_type_id: str
    volume: float
    total: float
    count: float
    date: str
    created_on: datetime
    updated_on: Optional[datetime]
    id: int = 0


class Parser:

    def __init__(self, site):
        self.site = site
        self.reports_dir = "reports"
        self.re_pattern = re.compile(r"href=\"([^\"]+)\"")

    @staticmethod
    async def fetch_data(url, encoding: str = "utf-8"):
        """Fetch HTML page from given URL."""
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            response = await loop.run_in_executor(pool, urlopen, url)
            logger.debug("parsing url %s", url)
            return response.read().decode(encoding).splitlines()

    @staticmethod
    async def parse_by_expression(data, expression):
        """Collect items from HTML page by given expression."""
        logger.debug("parsing data by expression %s", expression)
        return [line for line in data if expression in line]

    async def get_urls_from_retrieved_data(
            self, data, site_prefix: bool = True
    ):
        collected_urls = []
        for item in data:
            if matched_url := re.search(self.re_pattern, item):
                if site_prefix:
                    collected_urls.append(
                        f"{self.site}{matched_url.group(1).split('?')[0]}"
                    )
                else:
                    collected_urls.append(matched_url.group(1).split('?')[0])
        return collected_urls

    async def collect_reports(self, report_url, report_name):
        os.makedirs("reports", exist_ok=True)
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            if not os.path.exists(os.path.join(self.reports_dir, report_name)):
                logger.debug("report %s not found, downloading", report_name)
                await loop.run_in_executor(
                    pool, urlretrieve,
                    report_url, os.path.join(self.reports_dir, report_name)
                )
            logger.debug("report %s already exists, skipping", report_name)

    async def fetch_and_parse_data(self, page_num):
        page = await self.fetch_data(
            f"{self.site}/markets/oil_products/"
            f"trades/results/?page=page-{page_num}"
        )
        collected_data = await self.parse_by_expression(
            page,
            "/upload/reports/oil_xls/"
        )
        urls = await self.get_urls_from_retrieved_data(collected_data)
        return urls


def read_xls_file(path):
    instruments = []
    for item in path.glob("*.xls"):
        file = xlrd.open_workbook(item)
        sh = file.sheet_by_index(0)
        trade_date = sh.row_values(3)[1].split(":")[1]
        for row in range(sh.nrows):
            if (sh.row_values(row)[CONTRACT_VALUE_IDX] in (
                    "", "-", "Количество\nДоговоров,\nшт."
            ) or
                    sh.row_values(row)[1] in ("Итого:", "Итого по секции:")
            ):
                logger.debug("skipping row %s as non-relevant", row)
            else:
                try:
                    instrument = Instrument(
                        exchange_product_id=sh.cell_value(row, 1),
                        exchange_product_name=sh.cell_value(row, 2),
                        oil_id=sh.cell_value(row, 1)[:4],
                        delivery_basis_id=sh.cell_value(row, 1)[4:7],
                        delivery_basis_name=sh.cell_value(row, 3),
                        delivery_type_id=sh.cell_value(row, 1)[-1],
                        volume=float(sh.cell_value(row, 4)),
                        total=float(sh.cell_value(row, 5)),
                        count=float(sh.cell_value(row, CONTRACT_VALUE_IDX)),
                        date=trade_date,
                        created_on=datetime.now(),
                        updated_on=None,
                    )
                except Exception as e:
                    raise ValueError("exception in row %s: %s" %
                                     (sh.row_values(row), e))
                instruments.append(instrument)
    return instruments


async def main():
    parser = Parser(site="https://spimex.com")
    fetch_tasks = [
        parser.fetch_and_parse_data(page_num) for page_num in REPORTS_RANGE
    ]
    result = await asyncio.gather(*fetch_tasks)

    await asyncio.gather(*[parser.collect_reports(
        url, f"report_{url.split('/')[-1]}"
    ) for page in result for url in page])


if __name__ == '__main__':
    # asyncio.run(main())

    instruments = read_xls_file(REPORTS_DIR)

    print(instruments)
