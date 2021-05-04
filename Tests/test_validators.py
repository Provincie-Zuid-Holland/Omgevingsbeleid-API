from Endpoints import validators
import pytest
import marshmallow as MM
import io
import base64
import sys
from Tests.test_data import html_with_large_filesize_image

def test_HTML_Validator_XSS():
    with pytest.raises(MM.ValidationError) as val_error:
        evil_html ="""<IMG SRC=`javascript:alert("Hacker says, 'XSS'")`> Hello world! <a onload="eval(atob('ZG9jdW1lbnQubG9jYXRpb249Imh0dHA6Ly9saXN0ZXJuSVAvIitkb2N1bWVudC5jb29raWU='))" href=''>link</a>"""
        validators.HTML_Validate(evil_html)

def test_HTML_Validator_img_src():
    with pytest.raises(MM.ValidationError) as val_error:
        evil_html ="""<img src="https://www.images.net/photo.jpg">"""
        validators.HTML_Validate(evil_html)
    assert 'Non data uri for src' in str(val_error.value)

def test_HTML_Validator_img_size():
    with pytest.raises(MM.ValidationError) as val_error:
        evil_html = html_with_large_filesize_image
        validators.HTML_Validate(evil_html)
    assert 'Image filesize larger than' in str(val_error.value)

# def test_HTML_Validator_img_dimension():
#     with pytest.raises(MM.ValidationError) as val_error:
#         evil_html = html_with_oversized_width_image
#         validators.HTML_Validate(evil_html)
#     assert 'Image width larger than' in str(val_error.value)

