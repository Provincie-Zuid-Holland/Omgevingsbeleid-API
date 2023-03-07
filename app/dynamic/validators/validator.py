from abc import ABC, abstractmethod
from typing import Callable, Optional

from bs4 import BeautifulSoup


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
