import asyncio
import concurrent.futures
from datetime import datetime
import os
import re
import sys
import logging
from http import HTTPStatus
from http.client import HTTPResponse
from urllib.request import urlopen, urlretrieve
import pathlib
from typing import Any, Optional
from shutil import rmtree

import xlrd

from models import Instrument
from constants import (
    REPORTS_DIR,
    CONTRACT_VALUE_IDX,
    ROWS_TO_SKIP,
    EXCHANGE_PRODUCT_ID_COL,
    EXCHANGE_PRODUCT_NAME_COL,
    OIL_ID_SLICE,
    DELIVERY_BASIS_NAME_COL,
    DELIVERY_TYPE_ID_SLICE,
    DELIVERY_BASIS_ID_SLICE,
    VOLUME_COL,
    TOTAL_COL,
    COUNT_COL,
)


class ParserError(Exception):
    def __init__(self, item, error):
        super().__init__(f"Unable to parse item {item} due to error: {error}")


class InvalidDataException(Exception):
    def __init__(self, expected_type, actual_type):
        super().__init__(
            f"Expected an instance of {expected_type}, got {actual_type}."
        )


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())


class Parser:
    """
    Parser implementation for parsing HTML pages.

    This parser is implemented strictly for XLS files.
    """

    def __init__(self, site: str, pattern: Optional[str] = None):
        self.site = site
        self.re_pattern = pattern or re.compile(r"href=\"([^\"]+)\"")

    @classmethod
    def _check_incoming_data_type(cls, data: Any, expected_type: type) -> None:
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
                raise ParserError(url, exception) from exception
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

    async def _construct_url(self, url: str, site_prefix: bool) -> str:
        """
        Construct URL from a string, optionally adding site prefix.

        :param url: incoming piece of URL.
        :param site_prefix: flag for adding site prefix.
        :return: constructed URL.
        """
        if site_prefix:
            return f"{self.site}{url.split('?')[0]}"
        else:
            return url.split("?")[0]

    async def get_urls_from_retrieved_data(
        self, data: list[str], site_prefix: bool = True
    ) -> list[str]:
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
                collected_urls.append(
                    await self._construct_url(
                        matched_url.group(1), site_prefix
                    )
                )
        return collected_urls

    async def collect_reports(self, report_url: str, report_name: str) -> None:
        """
        Collect XLS files from given URL.

        If XLS file is not found, download it. Skip otherwise.

        This method is implemented in asynchronous way via `asyncio` module.

        :param report_url: URL of XLS file.
        :param report_name: name of XLS file to be saved with.
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


def get_sheet(path: pathlib.Path) -> xlrd.sheet.Sheet:
    """
    Open XLS-like file and return the very first sheet from it.

    :param path: Path to XLS file.
    :return: First sheet from the XLS file.
    """
    file = xlrd.open_workbook(path)
    sheet = file.sheet_by_index(0)
    return sheet


def get_instruments_from_sheet(sheet: xlrd.sheet.Sheet) -> list[Instrument]:
    """
    Get list of instruments from XLS sheet by specified indexes.

    :param sheet: Sheet to extract data from.
    :return: List of Instruments from specified sheet.
    """
    instruments = []
    trade_date = datetime.strptime(
        sheet.row_values(3)[1].split(":")[1].strip(), "%d.%m.%Y"
    )
    for row in range(sheet.nrows):
        if (
            sheet.row_values(row)[CONTRACT_VALUE_IDX] in ROWS_TO_SKIP
            or sheet.row_values(row)[1] in ROWS_TO_SKIP
        ):
            continue
        else:
            instruments.append(
                Instrument(
                    exchange_product_id=sheet.cell_value(
                        row, EXCHANGE_PRODUCT_ID_COL
                    ),
                    exchange_product_name=sheet.cell_value(
                        row, EXCHANGE_PRODUCT_NAME_COL
                    ),
                    oil_id=sheet.cell_value(row, EXCHANGE_PRODUCT_ID_COL)[
                        OIL_ID_SLICE
                    ],
                    delivery_basis_id=sheet.cell_value(
                        row, EXCHANGE_PRODUCT_ID_COL
                    )[DELIVERY_BASIS_ID_SLICE],
                    delivery_basis_name=sheet.cell_value(
                        row, DELIVERY_BASIS_NAME_COL
                    ),
                    delivery_type_id=sheet.cell_value(
                        row, EXCHANGE_PRODUCT_ID_COL
                    )[DELIVERY_TYPE_ID_SLICE],
                    volume=float(sheet.cell_value(row, VOLUME_COL)),
                    total=float(sheet.cell_value(row, TOTAL_COL)),
                    count=float(sheet.cell_value(row, COUNT_COL)),
                    date=trade_date,
                    created_on=datetime.now(),
                    updated_on=None,
                )
            )
    return instruments


def parse_xls_files(path: pathlib.Path, file_pattern: str) -> list[Instrument]:
    """
    Read XLS file and return list of instruments.

    This method parses through XLS file and gathers data about instruments
    on the way. Returns it as list of Instrument objects.

    :param path: Path-like format of *.xls file.
    :param file_pattern: file pattern/extension to iterate over.
    :return: list of instruments.
    """
    parsed_instruments = []
    for item in path.glob(file_pattern):
        try:
            sheet = get_sheet(item)
        except (xlrd.compdoc.CompDocError, IndexError) as exception:
            logger.exception("Cannot open doc %s", item)
            raise ParserError(item, exception) from exception
        try:
            parsed_instruments.extend(get_instruments_from_sheet(sheet))
        except ValueError as exception:
            logger.exception("Cannot parse sheet %s", sheet)
            raise ParserError(sheet, exception) from exception
    return parsed_instruments


def remove_reports_directory(directory: pathlib.Path) -> None:
    """Clear the directory after processing is done."""
    sys.stdout.write("Removing reports directory...\n")
    rmtree(directory)
    sys.stdout.write(f"{directory} was successfully removed.\n")


if __name__ == "__main__":
    print(
        get_instruments_from_sheet(
            get_sheet(
                pathlib.Path("reports/report_oil_xls_20230713162000.xls")
            )
        )
    )
