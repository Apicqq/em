import asyncio
import concurrent.futures
from datetime import datetime
import os
import re
import logging
from http import HTTPStatus
from http.client import HTTPResponse
from urllib.request import urlopen, urlretrieve
import pathlib
from typing import Any
import xlrd  # type: ignore

from models import Instrument #type: ignore


class ParserError(Exception):
    def __init__(self, item, error):
        super().__init__(f"Unable to parse item {item} due to error: {error}")


class InvalidDataException(Exception):
    def __init__(self, expected_type, actual_type):
        super().__init__(
            f"Expected an instance of {expected_type}, got {actual_type}."
        )


BASE_DIR = pathlib.Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_RANGE = range(45, 0, -1)
CONTRACT_VALUE_IDX = -1

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())


class Parser:
    """
    Parser implementation for parsing HTML pages.

    This parser is implemented strictly for XLS files.
    """

    def __init__(self, site):
        self.site = site
        self.re_pattern = re.compile(r"href=\"([^\"]+)\"")

    @classmethod
    def _check_incoming_data_type(cls, data: Any, expected_type: Any) -> None:
        if not isinstance(data, expected_type):
            raise InvalidDataException(expected_type, type(data))

    @staticmethod
    async def fetch_data(url: str, encoding: str = "utf-8") -> list[str]:
        """
        Fetch HTML page from given URL.

        Fetching of url is processed by `urlopen` method in asynchronous way.

        :param url: URL of HTML page.
        :param encoding: encoding of the HTML page. Defaults to `utf-8`.
        :return: list of lines of the HTML page.
        """
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                response: HTTPResponse = await loop.run_in_executor(
                    pool, urlopen, url
                )
                if response.getcode() != HTTPStatus.OK:
                    raise ConnectionError
            except ConnectionError as exception:
                logger.exception("failed to fetch url %s", url)
                raise ParserError(url, exception) from ConnectionError
            logger.debug("parsing url %s", url)
            return response.read().decode(encoding).splitlines()

    async def parse_by_expression(
        self, data: list[str], expression: str
    ) -> list[str]:
        """
        Collect items from HTML page by given expression.

        :param data: list of lines of the HTML page.
        :param expression: expression of the items to collect.
        :return: list of suitable items.
        """
        self._check_incoming_data_type(data, list)
        logger.debug("parsing data by expression %s", expression)
        return [line for line in data if expression in line]

    async def get_urls_from_retrieved_data(
        self, data: list[str], site_prefix: bool = True
    ):
        """
        Retrieve URLs from previously retrieved HTML pieces.

        Process of retrieving is implemented by regular expression.

        :param data: list of lines of the HTML page.
        :param site_prefix: flag for adding site prefix. Defaults to `True`.
        :return: list of URLs.
        """
        self._check_incoming_data_type(data, list)
        collected_urls = []
        for item in data:
            if matched_url := re.search(self.re_pattern, item):
                if site_prefix:
                    collected_urls.append(
                        f"{self.site}{matched_url.group(1).split('?')[0]}"
                    )
                else:
                    collected_urls.append(matched_url.group(1).split("?")[0])
        return collected_urls

    async def collect_reports(self, report_url: str, report_name: str) -> None:
        """
        Collect XLS files from given URL.

        If XLS file is not found, download it. Skip otherwise.

        This method is implemented in asynchronous way via `asyncio` module.

        :param report_url: URL of XLS file.
        :param report_name: name of XLS file.
        :return: None
        """
        self._check_incoming_data_type(report_url, str)
        self._check_incoming_data_type(report_name, str)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            if not os.path.exists(os.path.join(REPORTS_DIR, report_name)):
                logger.debug("report %s not found, downloading", report_name)
                await loop.run_in_executor(
                    pool,
                    urlretrieve,
                    report_url,
                    os.path.join(REPORTS_DIR, report_name),
                )
            logger.debug("report %s already exists, skipping", report_name)

    async def fetch_and_parse_data(self, page_num: int) -> list[str]:
        """
        Fetch and parse data from given URL.

        This method is implemented in asynchronous way via `asyncio` module.

        :param page_num: number of page to parse files from.
        :return: list of URLs that contain XLS files.
        """
        page = await self.fetch_data(
            f"{self.site}/markets/oil_products/"
            f"trades/results/?page=page-{page_num}"
        )
        collected_data = await self.parse_by_expression(
            page, "/upload/reports/oil_xls/"
        )
        urls = await self.get_urls_from_retrieved_data(collected_data)
        return urls


def read_xls_file(path: pathlib.Path) -> list[Instrument]:
    """
    Read XLS file and return list of instruments.

    This method parses through XLS file and gathers data about instruments
    on the way. Returns it as list of Instrument objects.

    :param path: Path-like format of *.xls file.
    :return: list of instruments.
    """
    instruments = []
    for item in path.glob("*.xls"):
        file = xlrd.open_workbook(item)
        sh = file.sheet_by_index(0)
        trade_date = datetime.strptime(
            sh.row_values(3)[1].split(":")[1].strip(), "%d.%m.%Y"
        ).date()
        for row in range(sh.nrows):
            if sh.row_values(row)[CONTRACT_VALUE_IDX] in (
                "",
                "-",
                "Количество\nДоговоров,\nшт.",
            ) or sh.row_values(row)[1] in ("Итого:", "Итого по секции:"):
                logger.debug("skipping row %s as non-relevant", row)
                continue
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
                except Exception as exception:
                    raise ParserError(item, exception)
                instruments.append(instrument)
    return instruments


async def main() -> None:
    """
    Main entrypoint to parser.

    Parser collects URLs of all XLS files and download them.
    """
    parser = Parser(site="https://spimex.com")
    fetch_tasks = [
        parser.fetch_and_parse_data(page_num) for page_num in REPORTS_RANGE
    ]
    result = await asyncio.gather(*fetch_tasks)

    await asyncio.gather(
        *[
            parser.collect_reports(url, f"report_{url.split('/')[-1]}")
            for page in result
            for url in page
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
