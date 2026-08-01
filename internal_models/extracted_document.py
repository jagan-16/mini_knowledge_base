from dataclasses import dataclass


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class ExtractedDocument:

    filename: str

    title: str | None

    author: str | None

    page_count: int

    pages: list[ExtractedPage]