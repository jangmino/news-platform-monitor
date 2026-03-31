"""HWPX 텍스트 추출기 — stdlib zipfile + xml.etree.ElementTree."""

from __future__ import annotations

import io
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional

import requests


# OWPML 네임스페이스
_NAMESPACES = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/content",
}


def _extract_text_from_xml(xml_content: bytes) -> str:
    """HWPX XML 콘텐츠에서 텍스트를 추출한다."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return ""

    texts = []
    # 다양한 태그 패턴에서 텍스트 추출
    for elem in root.iter():
        if elem.text and elem.text.strip():
            texts.append(elem.text.strip())
        if elem.tail and elem.tail.strip():
            texts.append(elem.tail.strip())

    return "\n".join(texts)


def extract_hwpx_from_bytes(data: bytes) -> Optional[str]:
    """바이트 데이터에서 HWPX 텍스트를 추출한다."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            texts = []
            # Contents/ 디렉토리의 섹션 파일들 탐색
            for name in sorted(zf.namelist()):
                if name.startswith("Contents/") and name.endswith(".xml"):
                    xml_data = zf.read(name)
                    text = _extract_text_from_xml(xml_data)
                    if text:
                        texts.append(text)

            if texts:
                return "\n\n".join(texts)
    except (zipfile.BadZipFile, KeyError, Exception):
        pass

    return None


def extract_hwpx_text(url: str, timeout: int = 30) -> Optional[str]:
    """URL에서 HWPX 파일을 다운로드하고 텍스트를 추출한다."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return extract_hwpx_from_bytes(response.content)
    except requests.RequestException:
        return None
