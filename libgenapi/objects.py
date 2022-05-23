from dataclasses import dataclass

@dataclass(repr=True, frozen=True)
class Comic:
    url: str
    published: str
    title: str


book_obj = {
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

book_keys = [
                "id",
                "author",
                "series_title_edition_and_isbn",
                "publisher",
                "year",
                "pages",
                "language",
                "size",
                "extension",
                "mirror",
                "mirror",
                "mirror",
                "mirror",
]