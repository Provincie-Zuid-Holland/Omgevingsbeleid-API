from dataclasses import dataclass


@dataclass
class ZipData:
    publication_filename: str
    filename: str
    binary: bytes
    checksum: str
