from pydantic import BaseModel

class BookSummary(BaseModel):
    book_id: str
    title: str
    descriptor: str | None
    cover_url: str | None


class Book(BaseModel):
    book_id: str
    title: str
    descriptor: str | None
    cover_url: str | None
    model: str | None
    created_at: str
    introduction: str | None
    appendix_prompt: str | None
    colophon: str | None
    card_display: dict


class EntryCard(BaseModel):
    order: int
    slug: str
    name: str
    descriptor: str | None
    metadata: dict


class Entry(BaseModel):
    order: int
    slug: str
    name: str
    descriptor: str | None
    content: str | None
    metadata: dict


class AdjacentEntry(BaseModel):
    slug: str
    name: str


class Navigation(BaseModel):
    prev: AdjacentEntry | None
    next: AdjacentEntry | None


class EntryWithNav(BaseModel):
    entry: Entry
    nav: Navigation


class SearchResult(BaseModel):
    """Search result with book context."""
    book_id: str
    book_title: str
    slug: str
    name: str
    descriptor: str | None
    score: float
