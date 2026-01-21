from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class Entry:
    order: int
    slug: str
    name: str
    descriptor: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    generated_at: Optional[str] = None
    error: Optional[str] = None

@dataclass
class Book:
    book_id: str
    title: str
    descriptor: str
    entries: List[Entry]
    system_prompt: str
    introduction: Optional[str] = None
    colophon: Optional[str] = None
    cover_path: Optional[str] = None
    card_display: Dict = field(default_factory=dict)
    model: str = ""
    created_at: Optional[str] = None

@dataclass
class PipelineContext:
    collection_id: str
    resume_from: int = 0
    skip_existing: bool = False
    workers: int = 5
    run_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    stats: Dict = field(default_factory=lambda: {
        "processed": 0,
        "failed": 0,
        "tokens_in": 0,
        "tokens_out": 0
    })
