import re


def generate_dso_gio_name(gio_title: str) -> str:
    s: str = gio_title.lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    s = s.replace(" ", "-")
    return s
