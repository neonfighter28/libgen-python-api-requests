# -*- coding: utf-8 -*-
"""
Library to search in Library Genesis
"""
import logging
import math
import random
import re
import sys
import time
import urllib

import bs4
import requests

import dummy as grab
from objects import book_obj as Book

# Logger settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.getLogger("requests.packages.urllib3").setLevel(logging.ERROR)

_FORMAT = "%(asctime)-5s %(levelname)s | %(funcName)30s | %(message)s"
logging.basicConfig(format=_FORMAT, datefmt="%H:%M:%S")

_REG_ISBN = r"(ISBN[-]*(1[03])*[ ]*(: ){0,1})*(([0-9Xx][- ]*){13}|([0-9Xx][- ]*){10})"
_REG_EDITION = r"(\[[0-9] ed\.\])"


class MissingMirrorsError(Exception):
    """
    Error shown when there are no mirrors.
    """


class MirrorsNotResolvingError(Exception):
    """
    Error shown when none of the mirrors are resolving.
    """


def _search(
        number_results: int = 25,
        _url: str = None,
        _params: dict = None,
        ):

    resp = requests.get(
        url=_url, params=_params
    )

    soup = bs4.BeautifulSoup(resp.text, features="lxml")

    # Find a nested tag in the second table element
    # containing the amount of results
    #
    # <body>
    #   <table></table>
    #   <table>"text to be extracted"</table>
    tag = soup.html.body.find_all("table")[1].text

    # Text of said tag starts with a digit (number of results)
    nbooks = int(re.search(r"\d+", tag).group())

    pages_to_load = int(number_results / 25.0)  # Pages needed to be loaded

    # Check if the pages needed to be loaded are more than the pages available
    if pages_to_load > int(math.ceil(nbooks / 25.0)):
        pages_to_load = int(math.ceil(nbooks / 25.0))
    search_result = []
    for page in range(1, pages_to_load + 1):
        if (
            len(search_result) > number_results
        ):  # Check if we got all the results
            break

        res = requests.get(
            _url + "/search.php?",
            params=_params.update({"page": page}),
        )
        text = res.content.decode()
        search_result += self.__parse(text)
        if page != pages_to_load:
            # Random delay because if you ask a lot of pages,your ip might get blocked.
            time.sleep(random.randint(250, 1000) / 1000.0)

    return search_result[:number_results]


class Libgenapi(object):
    """
    Main class representing the library
    TODO: Add documentation
    DONE -> Search multiple pages untile the number_results is meet or the end.
    TODO: Check for strange encodings, other langauges chinese,etc..
    TODO: Simplify,simplify,simply...For exemple the book dictionary should
    start with all keys with an empty string.
    TODO: Change the actual output to json?
    TODO: Make a example terminal app that uses it
    DONE: STARTED -> Add parameters to the search apart from the search_term
    TODO: Remove duplicate code. Reuse code between the different sections (LibGen,Scientific articles, Fiction,etc..).
    """

    class __Libgen(object):
        def __init__(self, url):
            self.url = url
            self.session = requests.Session()

        def __parse(self, doc):
            i = 0
            d_keys = Book.d_keys
            parse_result = []
            soup = bs4.BeautifulSoup(doc, features="lxml")
            table = soup.body.find_all("table")[2]
            for i, row in enumerate(table.find_all("tr")):
                if i >= 1:
                    book = {
                        "id": None,
                        "author": None,
                        "series": None,
                        "title": None,
                        "edition": None,
                        "isbn": None,
                        "publisher": None,
                        "year": None,
                        "pages": None,
                        "language": None,
                        "size": None,
                        "extension": None,
                        "mirrors": None,
                    }
                    values = row.find_all("td")
                    for i, value in enumerate(values):
                        if i > len(d_keys) - 1:
                            break
                        if d_keys[i] == "mirror":
                            mirror = value.find("a")["href"]
                            if len(mirror) > 0:
                                if book["mirrors"] is None:
                                    book["mirrors"] = [mirror]
                                else:
                                    book["mirrors"] += [mirror]
                                book["mirrors"][-1] = book["mirrors"][-1].replace(
                                    "../", self.url + "/"
                                )
                        elif d_keys[i] == "series_title_edition_and_isbn":
                            try:
                                # If there isn't an exception there is series,isbn or edition or all,
                                # now we have to separate it...
                                #
                                # Checking if there is any "green" text.
                                # If there is it means there is the title and something else.
                                # This raises an exception if there is no green text which is
                                # handled later on
                                value.find("a").find("font")["color"]

                                green_text = value.find_all("a")

                                book["title"] = value.find("a").text

                                # A regex I found for isbn, not sure if perfect but better than mine.
                                reg_isbn = re.compile(_REG_ISBN)
                                reg_edition = re.compile(_REG_EDITION)
                                for element in green_text:
                                    txt = str(element)

                                    if reg_isbn.search(txt) != None:  # isbn found
                                        book["isbn"] = [
                                            reg_isbn.search(_).group()
                                            for _ in element.text.split(",")
                                            if reg_isbn.search(_) != None
                                        ]
                                    elif (
                                        reg_edition.search(txt) != None
                                    ):  # edition found
                                        book["edition"] = element.text
                                    else:  # Series found
                                        book["series"] = element.text
                            except TypeError:
                                book["title"] = value.text
                        else:
                            book[d_keys[i]] = value.text

                    parse_result += [book]
            return parse_result

        def search(self, search_term, column="title", number_results=25):
            """Searches the mirror for the passed query

            Args:
                search_term (str): Search term for the library
                column (str, optional): Column to search. Defaults to "title".
                number_results (int, optional): Number of results per page. Defaults to 25.

            Returns:
                dict: Dictionary containing the book details
            """
            resp = self.session.get(
                self.url + "/search.php", params={"req": search_term, "column": column}
            )

            soup = bs4.BeautifulSoup(resp.content.decode(), features="lxml")

            # Find a nested tag in the second table element
            # containing the amount of results
            #
            # <body>
            #   <table></table>
            #   <table>"text to be extracted"</table>
            tag = soup.html.body.find_all("table")[1].text

            # Text of said tag starts with a digit (number of results)
            nbooks = int(re.search(r"\d+", tag).group())

            pages_to_load = int(number_results / 25.0)  # Pages needed to be loaded

            # Check if the pages needed to be loaded are more than the pages available
            if pages_to_load > int(math.ceil(nbooks / 25.0)):
                pages_to_load = int(math.ceil(nbooks / 25.0))
            search_result = []
            for page in range(1, pages_to_load + 1):
                if (
                    len(search_result) > number_results
                ):  # Check if we got all the results
                    break

                res = self.session.get(
                    self.url + "/search.php?",
                    params={"req": search_term, "column": column, "page": page},
                )
                text = res.content.decode()
                search_result += self.__parse(text)
                if page != pages_to_load:
                    # Random delay because if you ask a lot of pages,your ip might get blocked.
                    time.sleep(random.randint(250, 1000) / 1000.0)

            return search_result[:number_results]

    class __Scimag(object):
        def __init__(self, url):
            self.url = url

        def __parse(self, g):
            soup = bs4.BeautifulSoup(g, features="lxml")
            article = {
                "doi": None,
                "author": None,
                "article": None,
                "doi_owner": None,
                "journal": None,
                "issue": {
                    "year": None,
                    "month": None,
                    "day": None,
                    "volume": None,
                    "issue": None,
                    "first_page": None,
                    "last_page": None,
                },
                "issn": None,
                "size": None,
                "mirrors": [],
            }
            i = 0
            d_keys = [
                "doi_and_mirrors",
                "author",
                "article",
                "doi_owner",
                "journal",
                "issue",
                "issn",
                "size",
            ]
            parse_result = []
            for resultRow in soup.html.body.find("table", class_="catalog").find("tbody").find_all("tr"):
                article = {
                    "doi": None,
                    "author": None,
                    "article": None,
                    "doi_owner": None,
                    "journal": None,
                    "issue": {
                        "year": None,
                        "month": None,
                        "day": None,
                        "volume": None,
                        "issue": None,
                        "first_page": None,
                        "last_page": None,
                    },
                    "issn": None,
                    "size": None,
                    "mirrors": [],
                }
                i = 0
                for resultColumn in resultRow.find_all("td"):
                    #print(resultColumn)
                    if i > len(d_keys) - 1:
                        break
                    #print(resultRow)
                    if d_keys[i] == "doi_and_mirrors":  # Getting doi and mirrors links
                        mirrors = resultRow.find("ul").find_all("a", href=True)
                        article["doi"] = [mirror["href"] for mirror in mirrors]
                    elif d_keys[i] == "issn":
                        article["issn"] = resultColumn.select("*/text()").node_list()
                    elif d_keys[i] == "issue":
                        temp = [
                            x.split(":")[1]
                            for x in resultColumn.select("text()").node_list()
                        ]
                        # TODO: Assert these actually work
                        article["issue"]["year"] = temp[0]
                        article["issue"]["month"] = temp[1]
                        article["issue"]["day"] = temp[2]
                        article["issue"]["volume"] = re.search(r"(?<=volume\s)\d+", str(resultRow)).group()
                        article["issue"]["issue"] = re.search(r"(?<=issue\s)\d+", str(resultRow)).group()
                        article["issue"]["first_page"] = temp[5]
                        article["issue"]["last_page"] = temp[6]
                    else:
                        article[d_keys[i]] = resultColumn.text
                    i += 1
                parse_result += [article]
            return parse_result

        def search(
            self,
            search_term="",
            journal_title_issn="",
            volume_year="",
            issue="",
            pages="",
            number_results=25,
        ):
            """Search scimag

            Args:
                search_term (str, optional): Search term. Defaults to "".
                journal_title_issn (str, optional): journal title. Defaults to "".
                volume_year (str, optional): volume year. Defaults to "".
                issue (str, optional): issue. Defaults to "".
                pages (str, optional): pages. Defaults to "".
                number_results (int, optional): number of results. Defaults to 25.

            Returns:
                list[dict]: Search Results
            """
            """
                return _search(
                    _url=self.url,
                    _params={
                        "search_term": search_term,
                        "journal_title_issn": journal_title_issn,
                        "volume_year": volume_year,
                        "issue": issue,
                        "pages": pages,
                    },
                )
            """
            resp = requests.get(
                url=self.url,
                params={
                    "s": search_term,
                    "journalid": journal_title_issn,
                    "v": volume_year,
                    "i": issue,
                    "p": pages,
                    "redirect": "0",
                },
            )
            content = resp.content.decode()
            soup = bs4.BeautifulSoup(content, features="lxml")
            search_result = []
            # body > font:nth-child(7) Displayed first  100  results
            # body > font:nth-child(7) Found 1 results
            nresults = re.search(
                r"\d+", soup.html.body.find("div", class_="catalog_paginator").find("div", style="float:left").text
            ).group()

            nresults = int(nresults)
            pages_to_load = int(
                math.ceil(number_results / 25.0)
            )  # Pages needed to be loaded
            # Check if the pages needed to be loaded are more than the pages available
            if pages_to_load > int(math.ceil(nresults / 25.0)):
                pages_to_load = int(math.ceil(nresults / 25.0))
            for page in range(1, pages_to_load + 1):
                if (
                    len(search_result) > number_results
                ):  # Check if we got all the results
                    break
                resp = requests.get(
                    url=self.url,
                    params={
                        "s": search_term,
                        "journalid": journal_title_issn,
                        "v": volume_year,
                        "i": issue,
                        "p": pages,
                        "redirect": "0",
                        "page": page
                    },
                )
                search_result += self.__parse(resp.content.decode())
                if page != pages_to_load:
                    # Random delay because if you ask a lot of pages,your ip might get blocked.
                    time.sleep(random.randint(250, 1000) / 1000.0)
            return search_result[:number_results]

    class __Fiction(object):
        def __init__(self, url):
            self.url = url

        def __parse(self, g):
            soup = bs4.BeautifulSoup(g, features="lxml")
            book = {
                "author": None,
                "series": None,
                "title": None,
                "language": None,
                "libgenID": None,
                "size": None,
                "fileType": None,
                "timeAdded": None,
                "mirrors": [],
            }
            i = 0
            d_keys = [
                "author",
                "series",
                "title",
                "language",
                "libgenID_size_fileType_timeAdded_mirrors",
            ]

            parse_result = []
            for resultRow in soup.html.body.find("table", class_="catalog").tbody.find_all("tr"):
                book = {
                    "author": None,
                    "series": None,
                    "title": None,
                    "language": None,
                    "size": None,
                    "timeAdded": None,
                    "mirrors": [],
                }

                for i, resultColumn in enumerate(resultRow.find_all("td")):
                    if i > len(d_keys) - 1:
                        break
                    if d_keys[i] == "libgenID_size_fileType_timeAdded_mirrors":  # Getting Libgen Id, size, fileType, time Added and mirror links.
                        for mirror in resultRow.find("ul", class_="record_mirrors_compact").find_all("a", href=True):
                            book["mirrors"] += [mirror["href"]]

                        book["timeAdded"] = resultRow.find("td", title=True)["title"]
                        data = resultRow.find("td", title=True).text
                        book["fileType"] = re.search(r"\w+", data).group()
                        book["size"] = re.search(r"\d+\s\w+", data).group()

                    else:
                        book[d_keys[i]] = resultColumn.text.strip("\n")
                parse_result += [book]
            return parse_result

        def search(self, search_term="", pages="", number_results=25, _params=None):
            resp = requests.get(
                url=self.url,
                params={
                    "s": search_term,
                    "p": pages,
                },
            )
            content = resp.content.decode()
            soup = bs4.BeautifulSoup(content, features="lxml")
            search_result = []
            # body > font:nth-child(7) Displayed first  100  results
            # body > font:nth-child(7) Found 1 results
            nresults = re.search(
                r"\d+", soup.html.body.find("div", class_="catalog_paginator").find("div", style="float:left").text
            ).group()

            nresults = int(nresults)
            pages_to_load = int(
                math.ceil(number_results / 25.0)
            )  # Pages needed to be loaded
            # Check if the pages needed to be loaded are more than the pages available
            if pages_to_load > int(math.ceil(nresults / 25.0)):
                pages_to_load = int(math.ceil(nresults / 25.0))
            for page in range(1, pages_to_load + 1):
                if (
                    len(search_result) > number_results
                ):  # Check if we got all the results
                    break
                resp = requests.get(
                    url=self.url,
                    params={
                        "s": search_term,
                        "p": pages,
                        "page": page
                    },
                )
                search_result += self.__parse(resp.content.decode())
                if page != pages_to_load:
                    # Random delay because if you ask a lot of pages,your ip might get blocked.
                    time.sleep(random.randint(250, 1000) / 1000.0)
            return search_result[:number_results]

    class __Comics(object):
        def __init__(self, url):
            self.url = url

        def __parse(self, g):
            doc = g.doc
            comic = {
                "cover": None,
                "mirrors": [],
                "title": None,
                "size": None,
                "filetype": None,
                "dateAdded": None,
                "scanDpi": None,
                "scanPixels": None,
                "pages_nfiles": None,
                "pages_npictures": None,
                "comicsDOTorg": None,
            }
            i = 0
            d_keys = [
                "cover",
                "mirrors",
                "http_mirror_and_title",
                "size_filetype",
                "dateAdded",
                "scanDpi_and_scanPixels",
                "pages",
                "comicsDOTorg",
            ]
            parse_result = []
            for resultRow in doc.select("/html/body/table[2]/tr"):
                i = 0
                comic = {
                    "cover": None,
                    "mirrors": [],
                    "title": None,
                    "size": None,
                    "filetype": None,
                    "dateAdded": None,
                    "scanDpi": None,
                    "scanPixels": None,
                    "pages_nfiles": None,
                    "pages_npictures": None,
                    "comicsDOTorg": None,
                }
                for resultColumn in resultRow.select("td"):
                    if i > len(d_keys) - 1:
                        break
                    if d_keys[i] == "mirrors":  # Getting mirrors.
                        mirrors = resultColumn.select("font/a/@href")
                        for mirror in mirrors:
                            comic["mirrors"] += [g.make_url_absolute(mirror.text())]
                    elif (
                        d_keys[i] == "http_mirror_and_title"
                    ):  # Getting http mirror link and title.
                        # http_mirror = resultColumn.select("font/a/@href")[0].text()
                        # comic["mirrors"] += [http_mirror]
                        comic["title"] = resultColumn.select(
                            "descendant-or-self::text()"
                        ).node_list()[0]
                    elif d_keys[i] == "size_filetype":  # Getting size and filetype.
                        comic["size"] = resultColumn.select("text()[1]").text()
                        comic["filetype"] = resultColumn.select("text()[2]").text()
                    elif (
                        d_keys[i] == "scanDpi_and_scanPixels"
                    ):  # Getting scan size in pixels and scan dpi.
                        comic["scanPixels"] = resultColumn.select("font/a")[0].text()
                        comic["scanDpi"] = resultColumn.select("font/a")[2].text()
                    elif d_keys[i] == "cover":  # Gettin
                        comic["cover"] = g.make_url_absolute(
                            resultColumn.select("a/img/@src").text()
                        )
                    elif d_keys[i] == "pages":  # Getting pages info.
                        comic["pages_nfiles"] = resultColumn.select("font/a")[0].text()
                        comic["pages_npictures"] = resultColumn.select("font/a")[
                            2
                        ].text()
                    else:
                        comic[d_keys[i]] = resultColumn.text()
                    i += 1
                parse_result += [comic]
            return parse_result

        def search(self, search_term="", pages="", number_results=25):
            # TODO: Add Batch search for comics.
            g = grab.Grab()
            request = {"s": search_term, "p": pages}
            if sys.version_info[0] < 3:
                url = self.url + "?" + urllib.urlencode(request)
            else:
                url = self.url + "?" + urllib.parse.urlencode(request)
            g.go(url)
            search_result = []
            nresults = re.search(
                r"([0-9]*) results", g.doc.select("/html/body/font[1]").one().text()
            )

            nresults = int(nresults.group(1))
            pages_to_load = int(
                math.ceil(number_results / 25.0)
            )  # Pages needed to be loaded
            # Check if the pages needed to be loaded are more than the pages available
            if pages_to_load > int(math.ceil(nresults / 25.0)):
                pages_to_load = int(math.ceil(nresults / 25.0))
            for page in range(1, pages_to_load + 1):
                if (
                    len(search_result) > number_results
                ):  # Check if we got all the results
                    break
                url = ""
                request.update({"page": page})
                if sys.version_info[0] < 3:
                    url = self.url + "?" + urllib.urlencode(request)
                else:
                    url = self.url + "?" + urllib.parse.urlencode(request)
                g.go(url)
                search_result += self.__parse(g)
                if page != pages_to_load:
                    # Random delay because if you ask a lot of pages,your ip might get blocked.
                    time.sleep(random.randint(250, 1000) / 1000.0)
            return search_result[:number_results]

    def __init__(self, mirrors=None, debug=False):
        self.mirrors = mirrors
        self.__selected_mirror = None
        self.libgen = None
        self.scimag = None
        self.fiction = None
        self.comics = None
        self.standarts = None
        self.magzdb = None
        self.session = requests.Session()
        if debug:
            logger.setLevel(logging.DEBUG)

        if mirrors != None and len(mirrors) > 0:
            self.__choose_mirror()

    def set_mirrors(self, list_mirrors):
        """
        Sets the mirrors of Libgen Genesis
        """
        self.mirrors = list_mirrors
        self.__choose_mirror()

    def __choose_mirror(self):
        logger.debug("%s", "Choosing mirrors")
        if self.mirrors is None:
            raise MissingMirrorsError("There are no mirrors!")
        if isinstance(self.mirrors, str):
            self.mirrors = [self.mirrors]

        for mirror in self.mirrors:
            try:
                url = mirror
                logger.debug("%s", f"Fetched url {url}")
                req = self.session.get(url)
                content = req.content.decode()

                soup = bs4.BeautifulSoup(content, features="lxml")
                td = soup.find_all("td")

                for tag in td:
                    if 'name="lg_topic"' in str(tag):
                        add = re.findall(r"(?<=href\=\")[^\"]*", str(tag))[0]
                        value = tag.input["value"]
                        logger.debug("%s", f"URL {value = }, {add = }")
                        if value == "libgen":
                            self.libgen = self.__Libgen(url + add)
                        elif value == "fiction":
                            self.fiction = self.__Fiction(url + add)
                        elif value == "scimag":
                            self.scimag = self.__Scimag(url + add)
                        elif value == "magzdb":
                            self.comics = self.__Comics(add)
                        else:
                            logger.warning("%s", "Unknown Value")

                self.__selected_mirror = mirror
                break
            except requests.RequestException:
                raise MirrorsNotResolvingError(
                    "None of the mirrors are resolving, check"
                    + "if they are correct or you have connection!"
                )

    def search(self, *args, **kwargs):
        logger.warning(
            "%s", "Deprecated method, use Libgenapi().libgen.search() instead"
        )
        return self.libgen.search(*args, **kwargs)
