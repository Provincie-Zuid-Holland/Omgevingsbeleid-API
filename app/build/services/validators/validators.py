import io
import re
from base64 import b64decode
from typing import List, Optional

from bs4 import BeautifulSoup
from PIL import Image
from pydantic import ValidationInfo
from pydantic_core import PydanticUseDefault

from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.core.db.session import SessionFactoryType, session_scope_with_context

from .types import PydanticValidator, Validator


class NoneToDefaultValueValidator(Validator):
    def get_id(self) -> str:
        return "none_to_default_value"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        def pydantic_none_to_default_validator(cls, value, info: ValidationInfo):
            if value is None:
                raise PydanticUseDefault()
            return value

        return PydanticValidator(
            mode="before",
            func=pydantic_none_to_default_validator,
        )


class LengthValidator(Validator):
    def get_id(self) -> str:
        return "length"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        min_length: Optional[int] = config.get("min", None)
        max_length: Optional[int] = config.get("max", None)

        def pydantic_length_validator(cls, value, info: ValidationInfo):
            if not isinstance(value, str):
                raise ValueError("Value must be a string")

            if min_length is not None:
                if len(value) < min_length:
                    raise ValueError("Value is too small")

            if max_length is not None:
                if len(value) > max_length:
                    raise ValueError("Value is too large")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_length_validator,
        )


class PlainTextValidator(Validator):
    def get_id(self) -> str:
        return "plain_text"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        def pydantic_plain_text_validator(cls, value, info: ValidationInfo):
            if value is None:
                return None

            if not isinstance(value, str):
                raise ValueError("Value must be a string")

            soup: BeautifulSoup = BeautifulSoup(value, "html.parser")
            if soup.find():
                raise ValueError("Value is not allowed to contain html")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_plain_text_validator,
        )


class FilenameValidator(Validator):
    def __init__(self):
        self._pattern = r"^[\w\-.]+$"

    def get_id(self) -> str:
        return "filename"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        def pydantic_filename_validator(cls, value, info: ValidationInfo):
            if value is None:
                return None

            if not isinstance(value, str):
                raise ValueError("Value must be a string")

            is_valid: bool = bool(re.match(self._pattern, value))
            if not is_valid:
                raise ValueError("Not a valid filename")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_filename_validator,
        )


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
                "table",
                "tbody",
                "tr",
                "td",
                "th",
            ]
        )

        # @todo: validate these
        self._allowed_attrs = set(["src", "alt", "rel", "target", "href"])
        self._allowed_styles = set(["color"])
        self._allowed_schemas = set(["data", "https", "http"])

    def get_id(self) -> str:
        return "html"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        def pydantic_html_validator(cls, value, info: ValidationInfo):
            if value is None:
                return None
            if not isinstance(value, str):
                raise ValueError("Value must be a string")

            soup: BeautifulSoup = BeautifulSoup(value, "html.parser")
            used_tags = set([tag.name for tag in soup.find_all()])
            invalid_tags = set.difference(used_tags, self._allowed_tags)
            if invalid_tags:
                raise ValueError("Invalid html tags used")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_html_validator,
        )


class ImageValidator(Validator):
    def get_id(self) -> str:
        return "image"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        max_width: int = config["max_width"]
        max_height: int = config["max_height"]
        max_kb: int = config["max_kb"]

        def pydantic_image_validator(cls, value, info: ValidationInfo):
            if not isinstance(value, str):
                return value

            soup: BeautifulSoup = BeautifulSoup(value, "html.parser")
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

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_image_validator,
        )


class NotEqualRootValidator(Validator):
    def get_id(self) -> str:
        return "not_equal_root"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        field_keys: str = config["fields"]
        allow_none: bool = config.get("allow_none", False)
        error_message: str = config["error_message"]

        def pydantic_neq_model_validator(self, info: ValidationInfo):
            field_values = [getattr(self, k) for k in field_keys]
            if allow_none:
                field_values = [v for v in field_values if v is not None]

            if len(field_values) != len(set(field_values)):
                raise ValueError(error_message)

            return self

        return PydanticValidator(
            mode="after",
            func=pydantic_neq_model_validator,
        )


class ObjectCodeExistsValidator(Validator):
    def __init__(self, session_factory: SessionFactoryType, object_static_repository: ObjectStaticRepository):
        self._session_factory: SessionFactoryType = session_factory
        self._object_static_repository: ObjectStaticRepository = object_static_repository

    def get_id(self) -> str:
        return "object_code_exists"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        def pydantic_validator_object_code_exists(cls, value, info: ValidationInfo):
            if value is None:
                return None

            if not isinstance(value, str):
                raise ValueError("Value must be a string")

            try:
                object_type, object_id = value.split("-", 1)
            except ValueError:
                raise ValueError("Value is not a valid Object_Code")

            with session_scope_with_context(self._session_factory) as session:
                object_static = self._object_static_repository.get_by_object_type_and_id(
                    session,
                    object_type,
                    object_id,
                )
                if not object_static:
                    raise ValueError("Object does not exist")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_validator_object_code_exists,
        )


class ObjectCodeAllowedTypeValidator(Validator):
    def get_id(self) -> str:
        return "object_code_allowed_type"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        allowed_object_types: List[str] = config.get("allowed_object_types", [])

        def pydantic_validator_object_code_allowed_type(cls, value, info: ValidationInfo):
            if value is None:
                return None

            if not isinstance(value, str):
                raise ValueError("Value must be a string")

            try:
                object_type, _ = value.split("-", 1)
            except ValueError:
                raise ValueError("Value is not a valid Object_Code")

            if object_type not in allowed_object_types:
                raise ValueError("Invalid object type")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_validator_object_code_allowed_type,
        )


class ObjectCodesExistsValidator(Validator):
    def __init__(self, session_factory: SessionFactoryType, object_static_repository: ObjectStaticRepository):
        self._session_factory: SessionFactoryType = session_factory
        self._object_static_repository: ObjectStaticRepository = object_static_repository

    def get_id(self) -> str:
        return "object_codes_exists"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        def pydantic_validator_object_codes_exists(cls, value, info: ValidationInfo):
            if value is None:
                return None

            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError("Value must be a list of strings")

            for object_code in value:
                try:
                    object_type, object_id = object_code.split("-", 1)
                except ValueError:
                    raise ValueError("Value is not a valid Object_Code")

                with session_scope_with_context(self._session_factory) as session:
                    object_static = self._object_static_repository.get_by_object_type_and_id(
                        session,
                        object_type,
                        object_id,
                    )
                    if not object_static:
                        raise ValueError("Object does not exist")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_validator_object_codes_exists,
        )


class ObjectCodesAllowedTypeValidator(Validator):
    def get_id(self) -> str:
        return "object_codes_allowed_type"

    def get_validator_func(self, config: dict) -> PydanticValidator:
        allowed_object_types: List[str] = config.get("allowed_object_types", [])

        def pydantic_validator_object_codes_allowed_type(cls, value, info: ValidationInfo):
            if value is None:
                return None

            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError("Value must be a list of strings")

            for object_code in value:
                try:
                    object_type, _ = object_code.split("-", 1)
                except ValueError:
                    raise ValueError("Value is not a valid Object_Code")

                if object_type not in allowed_object_types:
                    raise ValueError("Invalid object type")

            return value

        return PydanticValidator(
            mode="after",
            func=pydantic_validator_object_codes_allowed_type,
        )
