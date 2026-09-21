import base64
from io import BytesIO

from PIL import Image


class ImageService:

    @staticmethod
    def to_data_url(image: Image.Image) -> str:
        """
        Convert a PIL Image into a Base64 data URL.

        The image is kept in memory and is not written to disk.
        """

        buffer = BytesIO()

        # JPEG keeps the request size smaller than PNG for most
        # photographic/diagram images.
        image.save(
            buffer,
            format="JPEG",
            quality=90,
        )

        encoded_image = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return f"data:image/jpeg;base64,{encoded_image}"