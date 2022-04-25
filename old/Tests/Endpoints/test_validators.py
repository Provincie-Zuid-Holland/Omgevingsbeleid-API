# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import pytest
import marshmallow as MM
import io
import base64
import sys
from pathlib import Path

from Api.Endpoints import validators


class TestValidators:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self._image_folder = Path("./Tests/resources/images")

    def test_HTML_Validator_XSS(self):
        with pytest.raises(MM.ValidationError) as val_error:
            evil_html = """<IMG SRC=`javascript:alert("Hacker says, 'XSS'")`> Hello world! <a onload="eval(atob('ZG9jdW1lbnQubG9jYXRpb249Imh0dHA6Ly9saXN0ZXJuSVAvIitkb2N1bWVudC5jb29raWU='))" href=''>link</a>"""
            validators.HTML_Validate(evil_html)

    def test_HTML_Validator_img_src(self):
        with pytest.raises(MM.ValidationError) as val_error:
            evil_html = """<img src="https://www.images.net/photo.jpg">"""
            validators.HTML_Validate(evil_html)
        assert "Non data uri for src" in str(val_error.value)

    def test_HTML_Validator_img_size(self):
        with open(self._image_folder / "zuidholland_large.png", "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            html_with_large_filesize_image = (
                f"""<h1>Happy</h1><img alt="" src="data:image/png;base64,{encoded}" />"""
            )

            with pytest.raises(MM.ValidationError) as val_error:
                evil_html = html_with_large_filesize_image
                validators.HTML_Validate(evil_html)
                assert "Image filesize larger than" in str(val_error.value)

    def test_HTML_Validator_img_dimension(self):
        with open(self._image_folder / "zuidholland_wide.jpg", "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            html_with_oversized_width_image = (
                f"""<h1>Happy</h1><img alt="" src="data:image/jpeg;base64,{encoded}" />"""
            )

            with pytest.raises(MM.ValidationError) as val_error:
                evil_html = html_with_oversized_width_image
                validators.HTML_Validate(evil_html)
                assert 'Image width larger than' in str(val_error.value)
