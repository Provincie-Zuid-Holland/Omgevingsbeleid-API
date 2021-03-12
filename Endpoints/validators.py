# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland
from marshmallow import ValidationError
from bs4 import BeautifulSoup, element
from urllib.parse import urlparse
from urllib import request
import sys
import base64
import io


whitelist_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'b', 'i',
                  'strong', 'li', 'ol', 'ul', 'img', 'br', 'u', 'em', 'span', 'sub']
whitelist_attrs = ['src', 'alt', 'rel', 'target']
whitelist_style = ['color']
whitelist_schema = ['data', 'https', 'http']


def bytesto(bytes, to, bsize=1024): 
    """converts bytes to a different units

    Args:
        bytes (bytes): The bytes to convert
        to (string): Target unit descriptor ('k' for kb, 'm' for mb, 'g' for gb)
        bsize (int, optional): Defaults to 1024.

    Returns:
        [type]: [description]
    """
    a = {'k' : 1, 'm': 2, 'g' : 3 }
    r = float(bytes)
    return bytes / (bsize ** a[to])


def HTML_Validate(s):
    """Validator that checks HTML for invalid input. Also ensures that no URL's are in the text

    Args:
        s (string): the input to validate
    """
    soup = BeautifulSoup(s, 'html.parser')
    for el in soup.descendants:
        if isinstance(el, element.Tag):
            if el.name not in whitelist_tags:
                raise ValidationError(
                    f'Non whitelisted tag "{el.name}" in text "{el}"')
            for attr, val in el.attrs.items():
                if attr == 'style':
                    style_lines = val.split(";")
                    for style in style_lines:
                        if style:
                            style_name = style.split(":")[0]
                            if style_name not in whitelist_style:
                                raise ValidationError(
                                    f'Non whitelisted style attribute "{style_name}" in text "{el}"')
                    continue
                elif attr not in whitelist_attrs:
                    raise ValidationError(
                        f'Non whitelisted attribute "{attr}" in text "{el}"')
                uri_parts = urlparse(val)
                if all([uri_parts.scheme, uri_parts.netloc, uri_parts.path]):
                    if uri_parts.scheme not in whitelist_schema:
                        raise ValidationError(
                            f'Non whitelisted url schema "{val}" in text "{el}"')

            if el.name == 'img':
                if 'src' in el.attrs:
                    val = el.attrs['src']
                    uri_parts = urlparse(val)
                    if not uri_parts.scheme == 'data':
                        raise ValidationError(f'Non data uri for src of image "{val}" in text "{el}"')
                    header, encoded_picture = el['src'].split(',', 1)
                    picture_data = base64.b64decode(encoded_picture)
                    if bytesto(sys.getsizeof(picture_data), 'm') > 1:
                        raise ValidationError(f'Image larger than 1MB in text')

            
        else:
            # Only need to check tags
            continue
