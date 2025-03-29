from pydantic import BaseModel


class ImageMeta(BaseModel):
    ext: str
    width: int
    height: int
    size: int

    def to_dict(self) -> dict:
        return {
            "ext": self.ext,
            "width": self.width,
            "height": self.height,
            "size": self.size,
        }
