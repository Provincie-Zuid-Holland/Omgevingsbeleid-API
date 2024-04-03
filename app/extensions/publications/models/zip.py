from dataclasses import dataclass


@dataclass
class ZipData:
    Publication_Filename: str
    Filename: str
    Binary: bytes
    Checksum: str
