from abc import ABCMeta, abstractmethod
from typing import Dict, List


class TextTemplate(metaclass=ABCMeta):
    @abstractmethod
    def get_free_text_template(self) -> str:
        pass

    @abstractmethod
    def get_object_templates(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def get_object_types(self) -> List[str]:
        pass
