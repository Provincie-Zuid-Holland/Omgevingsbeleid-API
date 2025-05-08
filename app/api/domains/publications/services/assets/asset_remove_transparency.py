import base64
import re
from io import BytesIO
from typing import Tuple

from PIL import Image


class AssetRemoveTransparency:
    def fix(self, content: str, meta: dict) -> Tuple[str, dict]:
        if meta["ext"] != "png":
            return content, meta

        try:
            base64_format_match = re.match(r"data:image/(.*?);base64,(.*)", content)
            mime_type, base64_data = base64_format_match.groups()

            original_image_data = base64.b64decode(base64_data)
            original_image = Image.open(BytesIO(original_image_data))

            has_transparency = original_image.mode == "RGBA" or "transparency" in original_image.info
            if not has_transparency:
                return content, meta

            rgb_image = Image.new("RGB", original_image.size, (255, 255, 255))
            if original_image.mode == "RGBA":
                mask = original_image.split()[3]
                rgb_image.paste(original_image, (0, 0), mask=mask)
            else:
                rgb_image.paste(original_image, (0, 0))

            # Convert back to base64
            rgb_image_arr = BytesIO()
            rgb_image.save(rgb_image_arr, format="PNG")
            rgb_image_arr = rgb_image_arr.getvalue()

            new_content = base64.b64encode(rgb_image_arr).decode()
            new_content = f"data:image/{mime_type};base64,{new_content}"

            meta["size"] = len(rgb_image_arr)

            return new_content, meta
        except Exception as e:
            raise e
