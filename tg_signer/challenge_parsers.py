from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Literal


@dataclass(frozen=True)
class OrderedButtonChallenge:
    direction: Literal["left_to_right", "right_to_left"]
    targets: tuple[str, ...]


_RIGHT_TO_LEFT_RE = re.compile(
    r"(?:从|自|由)\s*右\s*(?:到|往|向|至)\s*左|right\s*(?:to|-|→)\s*left",
    re.IGNORECASE,
)
_LEFT_TO_RIGHT_RE = re.compile(
    r"(?:从|自|由)\s*左\s*(?:到|往|向|至)\s*右|left\s*(?:to|-|→)\s*right",
    re.IGNORECASE,
)
_CLICK_MARKER_RE = re.compile(r"(?:依次|按顺序)?\s*点击\s*[:：]", re.IGNORECASE)
_VARIATION_SELECTORS_RE = re.compile("[\ufe0e\ufe0f]")
_OCR_PREFIX_RE = re.compile(
    r"^(?:(?:识别(?:结果)?|验证码|图片(?:中的)?文字|图片文字|文字|结果)"
    r"\s*(?:为|是|如下|[:：=])*\s*|"
    r"(?:the\s+)?(?:recognized\s+)?(?:captcha|code|text|result)"
    r"(?:\s+in\s+the\s+image)?\s*(?:is|[:：=])*\s*)",
    re.IGNORECASE,
)


def normalize_button_symbol(value: str) -> str:
    """Normalize presentation differences without changing the symbol itself."""
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    normalized = _VARIATION_SELECTORS_RE.sub("", normalized)
    return "".join(char for char in normalized if not char.isspace())


def _challenge_suffix(text: str, direction_end: int) -> str:
    marker = _CLICK_MARKER_RE.search(text, direction_end)
    if marker:
        return text[marker.end() :]
    colon_positions = [
        position
        for separator in ("：", ":")
        if (position := text.find(separator, direction_end)) >= 0
    ]
    if not colon_positions:
        return ""
    return text[min(colon_positions) + 1 :]


def parse_ordered_button_challenge(
    text: str,
    button_texts: Iterable[str],
) -> OrderedButtonChallenge | None:
    """Extract a left/right ordered target list by matching only real buttons."""
    text = str(text or "")
    rtl_match = _RIGHT_TO_LEFT_RE.search(text)
    ltr_match = _LEFT_TO_RIGHT_RE.search(text)
    if rtl_match and (not ltr_match or rtl_match.start() <= ltr_match.start()):
        direction: Literal["left_to_right", "right_to_left"] = "right_to_left"
        direction_match = rtl_match
    elif ltr_match:
        direction = "left_to_right"
        direction_match = ltr_match
    else:
        return None

    suffix = normalize_button_symbol(_challenge_suffix(text, direction_match.end()))
    if not suffix:
        return None

    labels_by_normalized: dict[str, str] = {}
    for button_text in button_texts:
        original = str(button_text or "")
        normalized = normalize_button_symbol(original)
        if normalized:
            labels_by_normalized.setdefault(normalized, original)

    matches: list[tuple[int, int, int, str]] = []
    for label_order, (normalized, original) in enumerate(labels_by_normalized.items()):
        start = 0
        while (position := suffix.find(normalized, start)) >= 0:
            matches.append((position, -len(normalized), label_order, original))
            start = position + len(normalized)
    if not matches:
        return None

    matches.sort(key=lambda item: (item[0], item[1], item[2]))
    targets: list[str] = []
    occupied_until = -1
    for position, negative_length, _, original in matches:
        match_end = position - negative_length
        if position < occupied_until:
            continue
        targets.append(original)
        occupied_until = match_end
    if direction == "right_to_left":
        targets.reverse()
    return OrderedButtonChallenge(direction=direction, targets=tuple(targets))


def clean_captcha_ocr_text(value: str) -> str:
    """Keep only the recognized captcha characters and never send spaces."""
    text = str(value or "").strip()
    text = re.sub(r"^```(?:text|plain|plaintext)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip("`'\"“”‘’ \t\r\n")
    for _ in range(2):
        cleaned = _OCR_PREFIX_RE.sub("", text).strip()
        if cleaned == text:
            break
        text = cleaned
    return "".join(char for char in text if char.isalnum())
