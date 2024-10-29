import asyncio
import concurrent.futures
import os
import re
import logging
from http import HTTPStatus
from http.client import HTTPResponse
from urllib.request import urlopen, urlretrieve
from urllib.parse import urlunparse
import pathlib

BASE_DIR = pathlib.Path(__file__).parent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# response: HTTPResponse = urlopen("https://spimex.com/markets/oil_products/trades/results/?page=page-45")
#
#
# string = response.read().decode("utf-8").splitlines()
# pprint(string)
#
# print(json_obj)


#
#
# import json
# from urllib.request import urlopen
#
# url = "https://jsonplaceholder.typicode.com/posts"
# response = urlopen(url)
# if response.getcode() == 200:
#     data = json.loads(response.read().decode('utf-8'))
#     print(data)
# else:
#     print('Error fetching data')

# def fetch_data(url):
#     response: HTTPResponse = urlopen(url)
#     if response.getcode() == 200:
#         data = response.read().decode('utf-8').splitlines()
#         return data
#     else:
#         print('Error fetching data')
#
#
# obj = fetch_data(
#     "https://spimex.com/markets/oil_products/trades/results/?page=page-45")
#
#
# def parse_css_by_expression(data: list[str], expression: str) -> list[str]:
#     finds = []
#     for obj in data:
#         if expression in obj:
#             finds.append(obj)
#     return finds
#
#
# def get_urls_from_fetched_data(data: list[str]) -> list[str]:
#     urls = []
#     pattern = re.compile(r"href=\"([^\"]+)\"")
#     for item in data:
#         if matched_url := re.search(pattern, item):
#             urls.append(matched_url.group(1))
#     return urls
#
#
# def retrieve_file(url, filename):
#     return urlretrieve(url, BASE_DIR / filename)
#
#
# resolved_data = (parse_css_by_expression(obj, "/upload/reports/oil_xls/"))
#
# print(get_urls_from_fetched_data(resolved_data))
# # print(resolved_data)
#
# for url in get_urls_from_fetched_data(resolved_data):
#     print(retrieve_file(f"https://spimex.com{url}", url.split("/")[-1]))
#
#
# def collect_reports(path):
#     for url in range(1, 45, -1):
#         yield retrieve_file(
#             f"https://spimex.com/upload/reports/oil_xls/oil_{url}.xls",
#             f"oil_{url}.xls")


class Parser:

    def __init__(self, site):
        self.site = site
        self.reports_dir = "reports"

    @staticmethod
    async def fetch_data(url, encoding: str = "utf-8"):
        """Fetch HTML page from given URL."""
        # response: HTTPResponse = await urlopen(url)
        # if response.getcode() == HTTPStatus.OK:
        #     return response.read().decode(encoding).splitlines()
        # else:
        #     raise ConnectionError
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
        urls = []
        pattern = re.compile(r"href=\"([^\"]+)\"")
        for item in data:
            if matched_url := re.search(pattern, item):
                if site_prefix:
                    urls.append(
                        f"{self.site}{matched_url.group(1).split('?')[0]}"
                    )
                else:
                    urls.append(matched_url.group(1).split('?')[0])
        return urls

    async def collect_reports(self, report_url, report_name):
        os.makedirs("reports", exist_ok=True)
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            logger.debug("collecting report %s", report_name)
            await loop.run_in_executor(
                pool, urlretrieve,
                report_url, os.path.join(self.reports_dir, report_name)
            )

async def main():
    parser = Parser(site="https://spimex.com")
    tasks = []
    for page_num in range(45, 1, -1):
        page = await parser.fetch_data(
            f"{parser.site}/markets/oil_products/"
            f"trades/results/?page=page-{page_num}"
        )
        collected_data = await parser.parse_by_expression(
            page,
            "/upload/reports/oil_xls/"
        )
        urls = await parser.get_urls_from_retrieved_data(collected_data)
        for url in urls:
            report_name = f"report_{url.split('/')[-1]}"
            tasks.append(parser.collect_reports(url, report_name))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
