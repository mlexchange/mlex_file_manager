import base64
import concurrent.futures
import io
import os
from functools import partial

import numpy as np
from PIL import Image
from tiled.client import from_uri
from tiled.client.array import ArrayClient

from file_manager.dataset.dataset import Dataset

# Check if a static tiled client has been set
STATIC_TILED_URI = os.getenv("STATIC_TILED_URI", None)
STATIC_TILED_API_KEY = os.getenv("STATIC_TILED_API_KEY", None)
if STATIC_TILED_URI:
    STATIC_TILED_CLIENT = from_uri(STATIC_TILED_URI, api_key=STATIC_TILED_API_KEY)
else:
    STATIC_TILED_CLIENT = None


class TiledDataset(Dataset):
    def __init__(
        self,
        uri,
        cumulative_data_count,
    ):
        """
        Definition of a tiled data set
        """
        super().__init__(uri, cumulative_data_count)
        pass

    def to_dict(self):
        """
        Convert to dictionary
        Returns:
            Dictionary
        """
        return {
            "uri": self.uri,
            "cumulative_data_count": self.cumulative_data_count,
        }

    @classmethod
    def from_dict(cls, dataset_dict):
        """
        Create a new instance from dictionary
        Args:
            dataset_dict:           Dictionary
        Returns:
            New instance
        """
        return cls(dataset_dict["uri"], dataset_dict["cumulative_data_count"])

    @staticmethod
    def _get_tiled_client(
        tiled_uri, api_key=None, static_tiled_client=STATIC_TILED_CLIENT
    ):
        """
        Get the tiled client
        Args:
            tiled_uri:              Tiled URI
            api_key:                Tiled API key
            static_tiled_client:    Static tiled client
        Returns:
            Tiled client
        """
        # Checks if a static tiled client has been set, otherwise creates a new one
        if static_tiled_client:
            return static_tiled_client
        else:
            client = from_uri(tiled_uri, api_key=api_key)
            return client

    @classmethod
    def _log_image(cls, image, threshold=0.000000000001):
        """
        Process image
        Args:
            image:      PIL image
        Returns:
            PIL image
        """
        # Mask negative and NaN values
        nan_img = np.isnan(image)
        img_neg = image < 0.0
        mask_neg = np.array(img_neg)
        mask_nan = np.array(nan_img)
        mask = mask_nan + mask_neg
        x = np.ma.array(image, mask=mask)

        image = np.log(x + threshold)
        x = np.ma.array(image, mask=mask)

        x = cls._normalize_percentiles(x)
        return x

    @staticmethod
    def _normalize_percentiles(x, low_perc=0.01, high_perc=99):
        low = np.percentile(x.ravel(), low_perc)
        high = np.percentile(x.ravel(), high_perc)
        x = (np.clip((x - low) / (high - low), 0, 1) * 255).astype(np.uint8)
        return x

    def _process_image(self, image, log, resize, export):
        if log:
            image = self._log_image(image)
        elif image.dtype != np.uint8:
            image = self._normalize_percentiles(image)

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

    def read_data(
        self,
        root_uri,
        indexes,
        export="base64",
        resize=True,
        log=False,
        api_key=None,
        downsample=False,
        just_uri=False,
    ):
        """
        Read data set
        Args:
            root_uri:          Root URI from which data should be retrieved
            indexes:           Index or list of indexes of the images to retrieve
            export:            Export format, defaults to base64
            resize:            Resize image to 200x200, defaults to True
            log:               Apply log(1+x) to the image, defaults to False
            api_key:           Tiled API key
            downsample:        Downsample the image, defaults to False
            just_uri:          Return only the uri, defaults to False
        Returns:
            Base64/PIL image
            Dataset URI
        """
        if isinstance(indexes, int):
            indexes = [indexes]

        tiled_uris = self.get_tiled_uris(root_uri, indexes)
        if just_uri:
            return tiled_uris

        tiled_client = self._get_tiled_client(root_uri, api_key)
        tiled_data = tiled_client[self.uri]
        if downsample:
            if len(tiled_data.shape) == 4:
                block_data = tiled_data[indexes, :, ::10, ::10]
            elif len(tiled_data.shape) == 3:
                block_data = tiled_data[indexes, ::10, ::10]
            else:
                block_data = tiled_data[::10, ::10]
                block_data = np.expand_dims(block_data, axis=0)
        else:
            if len(tiled_data.shape) == 4:
                block_data = tiled_data[indexes]
            elif len(tiled_data.shape) == 3:
                block_data = tiled_data[indexes]
            else:
                block_data = tiled_data
                block_data = np.expand_dims(block_data, axis=0)

        if export == "raw":
            return block_data, tiled_uris

        # Check if there are 4 dimensions for a grayscale image
        if block_data.shape[1] == 1:
            block_data = np.squeeze(block_data, axis=1)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            data = list(
                executor.map(
                    self._process_image,
                    block_data,
                    [log] * len(indexes),
                    [resize] * len(indexes),
                    [export] * len(indexes),
                )
            )
        return data, tiled_uris

    def get_tiled_uris(self, root_uri, indexes):
        """
        Get tiled URIs
        Args:
            root_uri:          Root URI from which data should be retrieved
            indexes:           List of indexes of the images to retrieve
        Returns:
            List of tiled URIs
        """
        tiled_client = self._get_tiled_client(root_uri)
        base_tiled_uri = tiled_client[self.uri].uri
        if (
            len(tiled_client[self.uri].shape) > 2
            and tiled_client[self.uri].shape[0] > 1
        ):
            base_tiled_uri.replace("/metadata/", "/array/full/")
            return [f"{base_tiled_uri}?slice={index}" for index in indexes]
        else:
            return [base_tiled_uri]

    def get_uri_index(self, uri):
        """
        Get index of the URI
        Args:
            uri:          URI of the image
        Returns:
            Index of the URI
        """
        if "slice=" not in uri:
            return 0
        return int(uri.split("slice=")[-1])

    def _check_node(tiled_client, sub_uri, node):
        """
        Checks if the sub_uri exists in the node and returns the URI
        Args:
            tiled_client:       Current tiled client, which is used when the method is run
            sub_uri:           sub_uri to filter the data
            node:               Node to process
        Returns:
            URI of the node
        """
        try:
            tiled_client[f"/{node}/{sub_uri}"]
            return f"/{node}/{sub_uri}"
        except Exception:
            return None

    @staticmethod
    def _get_node_size(tiled_client, node):
        tiled_array = tiled_client[node]
        array_shape = tiled_array.shape
        if len(array_shape) == 2:
            return 1
        else:
            return array_shape[0]

    @classmethod
    def _get_cumulative_data_count(cls, tiled_client, nodes):
        """
        Retrieve tiled data sets from list of tiled_uris
        Args:
            tiled_uris:         Tiled URIs from which data should be retrieved
            api_key:            Tiled API key
        Returns:
            Length of the data set
        """
        get_node_size_with_client = partial(cls._get_node_size, tiled_client)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            sizes = list(executor.map(get_node_size_with_client, nodes))

        cumulative_dataset_size = [sum(sizes[: i + 1]) for i in range(len(sizes))]
        return cumulative_dataset_size

    @classmethod
    def browse_data(
        cls,
        root_uri,
        api_key=None,
        sub_uri_template="",
        selected_sub_uris=[""],
    ):
        """
        Retrieve a list of nodes from tiled URI
        Args:
            root_uri:                Root URI from which data should be retrieved
            api_key:                 Tiled API key
            sub_uri_template:        Template for the sub URI
            selected_sub_uris:       List of selected sub URIs
        Returns:
            tiled_uris:              List of tiled URIs found in tiled client
            cumulative_data_counts:  Cumulative data count
        """
        tiled_client = cls._get_tiled_client(root_uri, api_key)
        if selected_sub_uris != [""]:
            # Check if the selected sub URIs are nodes
            tmp_sub_uris = []
            for sub_uri in selected_sub_uris:
                if type(tiled_client[sub_uri]) is ArrayClient:
                    tmp_sub_uris.append(sub_uri)
                else:
                    tmp_sub_uris += [
                        f"{sub_uri}/{node}" for node in tiled_client[sub_uri]
                    ]
            selected_sub_uris = tmp_sub_uris

            # Get sizes of the selected nodes
            cumulative_data_counts = cls._get_cumulative_data_count(
                tiled_client,
                selected_sub_uris,
            )
            return selected_sub_uris, cumulative_data_counts

        # Browse the tiled URI
        tiled_uris = []
        nodes = list(tiled_client)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_node = {
                executor.submit(
                    cls._check_node, tiled_client, sub_uri_template, node
                ): node
                for node in nodes
            }
            for future in concurrent.futures.as_completed(future_to_node):
                uri = future.result()
                if uri is not None:
                    tiled_uris.append(uri)
        return tiled_uris, [0] * len(tiled_uris)
