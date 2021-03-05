from Endpoints import validators
import pytest
import marshmallow as MM
import io
import base64
import sys

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
        mem_image = io.BytesIO(b"")
        mem_image.seek(2740000) #about 2.1 MB
        mem_image.write(b"\0")
        mem_image.seek(0)
        encoded = base64.b64encode(mem_image.read()).decode('utf-8')
        evil_html =f"""<img src='data:image/png;base64,{encoded}' >"""
        validators.HTML_Validate(evil_html)
    assert 'Image larger than 5MB in text' in str(val_error.value)
