"""문서 첨부파일 텍스트 추출기 — HWPX, PDF, ODT 지원."""

from __future__ import annotations

import io

import requests

from src.collectors.hwpx_parser import extract_hwpx_text


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# 선택적 의존성 — 설치되지 않아도 다른 형식은 정상 동작
try:
    import fitz  # pymupdf

    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

try:
    from odf import teletype
    from odf import text as odf_text
    from odf.opendocument import load as odf_load

    _ODT_AVAILABLE = True
except ImportError:
    _ODT_AVAILABLE = False


def _fetch(url: str, timeout: int = 10) -> bytes | None:
    """URL에서 파일을 다운로드하여 바이트로 반환한다."""
    try:
        resp = requests.get(
            url, headers={"User-Agent": _USER_AGENT}, timeout=timeout
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def _extract_pdf(url: str) -> str | None:
    """PDF 파일에서 텍스트를 추출한다."""
    if not _PDF_AVAILABLE:
        return None
    data = _fetch(url)
    if not data:
        return None
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception:
        return None


def _extract_odt(url: str) -> str | None:
    """ODT 파일에서 텍스트를 추출한다."""
    if not _ODT_AVAILABLE:
        return None
    data = _fetch(url)
    if not data:
        return None
    try:
        odt_doc = odf_load(io.BytesIO(data))
        return "\n".join(
            teletype.extractText(p) for p in odt_doc.getElementsByType(odf_text.P)
        )
    except Exception:
        return None


def extract_doc_text(url: str, file_name: str) -> tuple[str | None, str]:
    """URL에서 문서를 다운로드하고 텍스트를 추출한다.

    Args:
        url: 첨부파일 URL
        file_name: 파일명 (확장자 판별용, 소문자 권장)

    Returns:
        (extracted_text, parse_status)
        parse_status: "success" | "failed" | "unsupported"
    """
    name = file_name.lower()

    if name.endswith(".hwpx"):
        text = extract_hwpx_text(url)
        return (text, "success") if text else (None, "failed")

    if name.endswith(".pdf"):
        text = _extract_pdf(url)
        return (text, "success") if text else (None, "failed")

    if name.endswith(".odt"):
        text = _extract_odt(url)
        return (text, "success") if text else (None, "failed")

    return None, "unsupported"
