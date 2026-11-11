"""Text helpers shared by the data loader and the search engine.

Everything we compare is first passed through `normalize()` so that
"Where's the ICT room?", "where is the ict room" and "ở đâu" (without
accents: "o dau") all become plain lowercase ASCII words.
"""

import re
import unicodedata

_NON_WORD = re.compile(r"[^a-z0-9:]+")


def strip_accents(text: str) -> str:
    """Remove Vietnamese (and other) accents: 'Thư viện' -> 'Thu vien'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def normalize(text: str) -> str:
    """Lowercase, remove accents and punctuation, collapse spaces."""
    text = strip_accents(text or "").lower()
    text = text.replace("'s", " ").replace("’s", " ")
    return " ".join(_NON_WORD.sub(" ", text).split())


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def has_vietnamese_accents(text: str) -> bool:
    """True if the text contains Vietnamese-specific letters or tone marks."""
    return any(ch != strip_accents(ch) for ch in text)


def split_list(value: str) -> list[str]:
    """CSV cells hold lists separated by ';' (e.g. 'ICT;Computer Science')."""
    return [part.strip() for part in (value or "").split(";") if part.strip()]
