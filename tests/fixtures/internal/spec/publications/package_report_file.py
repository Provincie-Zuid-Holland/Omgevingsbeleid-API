from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from tests.fixtures.internal.types import BASE_FILES_DIR

FILES_DIR: Path = BASE_FILES_DIR / "publication_package_reports"

NAMESPACES: dict[str, str] = {
    "lvbb": "http://www.overheid.nl/2017/lvbb",
    "stop": "http://www.overheid.nl/2017/stop",
}


@dataclass
class ParsedReportFile:
    filename: str
    source_document: str
    main_outcome: str
    sub_delivery_id: str
    sub_progress: str
    sub_outcome: str
    report_status: str


# Mirrors `_parse_report_xml` in the act/announcement report upload endpoints
def parse_report_file(file_path: str) -> ParsedReportFile:
    path = Path(FILES_DIR / file_path)
    content: bytes = path.read_bytes()
    root = etree.fromstring(content, None)

    main_outcome: str = root.xpath("//lvbb:uitkomst/text()", namespaces=NAMESPACES)[0]
    sub_delivery_id: str = root.xpath("//lvbb:verslag/lvbb:idLevering/text()", namespaces=NAMESPACES)[0]
    sub_progress: str = _xml_get(root, "//lvbb:verslag/lvbb:voortgang/text()")
    sub_outcome: str = _xml_get(root, "//lvbb:verslag/lvbb:uitkomst/text()")

    if root.xpath("//stop:code[text()='DL-0005']", namespaces=NAMESPACES):
        sub_outcome = sub_outcome or "Received code DL-0005"

    return ParsedReportFile(
        filename=path.name,
        source_document=content.decode("utf-8"),
        main_outcome=main_outcome,
        sub_delivery_id=sub_delivery_id,
        sub_progress=sub_progress,
        sub_outcome=sub_outcome,
        report_status="valid" if main_outcome == "succes" else "failed",
    )


def _xml_get(root, path: str) -> str:
    matches = root.xpath(path, namespaces=NAMESPACES)
    return matches[0] if matches else ""
