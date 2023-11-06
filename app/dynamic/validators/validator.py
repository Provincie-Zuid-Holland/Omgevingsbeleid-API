import io
from abc import ABC, abstractmethod
from base64 import b64decode
from typing import Callable, Optional

from bs4 import BeautifulSoup
from PIL import Image


class Validator(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_validator_func(self, config: dict) -> Callable:
        pass


class LengthValidator(Validator):
    def get_id(self) -> str:
        return "length"

    def get_validator_func(self, config: dict) -> Callable:
        min_length: Optional[int] = config.get("min", None)
        max_length: Optional[int] = config.get("max", None)

        def pydantic_length_validator(cls, v):
            if not isinstance(v, str):
                raise ValueError("Value must be a string")

            if min_length is not None:
                if len(v) < min_length:
                    raise ValueError("Value is too small")

            if max_length is not None:
                if len(v) > max_length:
                    raise ValueError("Value is too large")

            return v

        return pydantic_length_validator


class PlainTextValidator(Validator):
    def get_id(self) -> str:
        return "plain_text"

    def get_validator_func(self, config: dict) -> Callable:
        def pydantic_plain_text_validator(cls, v):
            if v is None:
                return v

            if not isinstance(v, str):
                raise ValueError("Value must be a string")

            soup: BeautifulSoup = BeautifulSoup(v, "html.parser")
            if soup.find():
                raise ValueError("Value is not allowed to contain html")

            return v

        return pydantic_plain_text_validator


class HtmlValidator(Validator):
    def __init__(self):
        self._allowed_tags = set(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "p",
                "b",
                "i",
                "a",
                "strong",
                "li",
                "ol",
                "ul",
                "img",
                "br",
                "u",
                "em",
                "span",
                "sub",
                "sup",
            ]
        )

        # @todo: validate these
        self._allowed_attrs = set(["src", "alt", "rel", "target", "href"])
        self._allowed_styles = set(["color"])
        self._allowed_schemas = set(["data", "https", "http"])

    def get_id(self) -> str:
        return "html"

    def get_validator_func(self, config: dict) -> Callable:
        def pydantic_plain_text_validator(cls, v):
            if not isinstance(v, str):
                raise ValueError("Value must be a string")

            soup: BeautifulSoup = BeautifulSoup(v, "html.parser")
            used_tags = set([tag.name for tag in soup.find_all()])
            invalid_tags = set.difference(used_tags, self._allowed_tags)
            if invalid_tags:
                raise ValueError("Invalid html tags used")

            return v

        return pydantic_plain_text_validator


class ImageValidator(Validator):
    def get_id(self) -> str:
        return "image"

    def get_validator_func(self, config: dict) -> Callable:
        max_width: int = config["max_width"]
        max_height: int = config["max_height"]
        max_kb: int = config["max_kb"]

        def pydantic_image_validator(cls, v):
            if not isinstance(v, str):
                return v

            soup: BeautifulSoup = BeautifulSoup(v, "html.parser")
            img_tags = soup.find_all("img")

            for tag in img_tags:
                img_data = tag["src"]

                # Check if image data is base64
                if not img_data.startswith("data:image"):
                    raise ValueError("Image data is not base64 encoded")

                # Get base64 data
                base64_data = img_data.split(",", 1)[1]
                img_bytes = b64decode(base64_data)

                # Check image size
                if len(img_bytes) / 1024 > max_kb:
                    raise ValueError("Image size is greater than max allowed")

                # Open image and check dimensions
                img = Image.open(io.BytesIO(img_bytes))
                if img.width > max_width or img.height > max_height:
                    raise ValueError("Image dimensions are greater than max allowed")

            return v

        return pydantic_image_validator


class NotEqualRootValidator(Validator):
    def get_id(self) -> str:
        return "not_equal_root"

    def get_validator_func(self, config: dict) -> Callable:
        field_keys: str = config["fields"]
        allow_none: bool = config.get("allow_none", False)
        error_message: str = config["error_message"]

        def pydantic_neq_root_validator(cls, values):
            field_values = [values[k] for k in field_keys]
            if allow_none:
                field_values = [v for v in field_values if v is not None]

            if len(field_values) != len(set(field_values)):
                raise ValueError(error_message)

            return values

        return pydantic_neq_root_validator
