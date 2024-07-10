import base64
import io

import numpy as np
from PIL import Image


class Dataset:
    def __init__(self, uri, cumulative_data_count):
        """
        Base class for data set schema definition
        Args:
            uri:                    Data set URI
            cumulative_data_count:  Cumulative data count
        """
        self.uri = uri
        self.cumulative_data_count = cumulative_data_count
        pass

    @staticmethod
    def _apply_log_transform(image, threshold=0.000000000001):
        # Mask negative and NaN values
        nan_img = np.isnan(image)
        img_neg = image < 0.0
        mask_neg = np.array(img_neg)
        mask_nan = np.array(nan_img)
        mask = mask_nan + mask_neg
        x = np.ma.array(image, mask=mask)

        # Normalize image
        x = x - np.min(x)
        x = np.ma.array(x, mask=mask)
        x = x / (np.max(x))
        x = np.ma.array(x, mask=mask)

        image = np.log(x + threshold)
        x = np.ma.array(image, mask=mask)
        return x

    @staticmethod
    def _normalize_percentiles(x, percentiles):
        low = np.percentile(x.ravel(), percentiles[0])
        high = np.percentile(x.ravel(), percentiles[1])
        if high - low > 0:
            x = (np.clip((x - low) / (high - low), 0, 1) * 255).astype(np.uint8)
        else:
            x = np.zeros_like(x, dtype=np.uint8)
        return x

    @classmethod
    def _process_image(cls, image, log, resize, export, percentiles):
        if log:
            image = cls._apply_log_transform(image)

        if percentiles != [0, 100]:
            image = cls._normalize_percentiles(image, percentiles)
        elif image.dtype != np.uint8:
            # Normalize image to 0-255
            image = (
                (image - np.min(image)) / (np.max(image) - np.min(image)) * 255
            ).astype(np.uint8)
        image = Image.fromarray(image)

        if resize:
            image = image.resize((200, 200))

        if export == "pillow":
            return image
        else:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            contents = buffered.getvalue()

        contents_base64 = base64.b64encode(contents).decode("utf-8")
        return f"data:image/png;base64,{contents_base64}"
