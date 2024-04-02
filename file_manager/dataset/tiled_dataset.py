import base64
import concurrent.futures
import io
import os
import time

import numpy as np
from PIL import Image
from tiled.client import from_uri
from tiled.client.array import ArrayClient

from file_manager.dataset.dataset import Dataset

# Check if a static tiled client has been set
STATIC_TILED_URI = os.getenv("STATIC_TILED_URI", None)
STATIC_TILED_API_KEY = os.getenv("STATIC_TILED_API_KEY", None)
if STATIC_TILED_URI:
    if STATIC_TILED_API_KEY:
        STATIC_TILED_CLIENT = from_uri(STATIC_TILED_URI, api_key=STATIC_TILED_API_KEY)
    else:
        STATIC_TILED_CLIENT = from_uri(STATIC_TILED_URI)
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
            if api_key:
                client = from_uri(tiled_uri, api_key=api_key)
            else:
                client = from_uri(tiled_uri)
            return client

    @staticmethod
    def _log_image(image, threshold=1):
        """
        Process image
        Args:
            image:      PIL image
        Returns:
            PIL image
        """
        image = image.astype(np.float32)
        image = np.log(image + threshold)
        image = (
            (image - np.min(image)) / (np.max(image) - np.min(image)) * 255
        ).astype(np.uint8)
        return image

    def _process_image(self, index, image, log, resize, export):
        if log:
            image = self._log_image(image)
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
        Returns:
            Base64/PIL image
            Dataset URI
        """
        if isinstance(indexes, int):
            indexes = [indexes]

        tiled_client = self._get_tiled_client(root_uri, api_key)
        tiled_data = tiled_client[self.uri]
        start = time.time()
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
        print(
            f"Time to read {len(indexes)} images of size {block_data.shape}: {time.time() - start}",
            flush=True,
        )

        if block_data.dtype != np.uint8:
            low = np.percentile(block_data.ravel(), 1)
            high = np.percentile(block_data.ravel(), 99)
            block_data = np.clip((block_data - low) / (high - low), 0, 1)
            block_data = (block_data * 255).astype(np.uint8)

        print(f"Shape: {block_data.shape}", flush=True)

        # Check if there are 4 dimensions for a grayscale image
        if block_data.shape[1] == 1:
            block_data = np.squeeze(block_data, axis=1)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            data = list(
                executor.map(
                    self._process_image,
                    indexes,
                    block_data,
                    [log] * len(indexes),
                    [resize] * len(indexes),
                    [export] * len(indexes),
                )
            )

        tiled_uris = self.get_tiled_uris(root_uri, indexes)
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
        if len(indexes) > 1:
            return [f"{root_uri}{self.uri}?slice={index}" for index in indexes]
        else:
            return [f"{root_uri}{self.uri}"]

    @staticmethod
    def _check_node(tiled_client, query, node):
        """
        Checks if the query exists in the node and returns the URI
        Args:
            tiled_client:       Current tiled client, which is used when the method is run
            query:              Query to filter the data
            node:               Node to process
        Returns:
            URI of the node
        """
        # TODO: SUBPATH instead of QUERY
        try:
            tiled_client[f"/{node}/{query}"]
            return f"/{node}/{query}"
        except Exception as e:
            print(e, flush=True)
            return None

    @staticmethod
    def _get_cumulative_data_count(tiled_client, nodes):
        """
        Retrieve tiled data sets from list of tiled_uris
        Args:
            tiled_uris:         Tiled URIs from which data should be retrieved
            api_key:            Tiled API key
        Returns:
            Length of the data set
        """
        sizes = []
        cumulative_dataset_size = 0
        for node in nodes:
            tiled_array = tiled_client[node]
            # TODO: check if there are more sub-containers
            if type(tiled_array) is ArrayClient:
                array_shape = tiled_array.shape
                if len(array_shape) == 2:
                    cumulative_dataset_size += 1
                else:
                    cumulative_dataset_size += array_shape[0]
            else:
                cumulative_dataset_size += 1
            sizes.append(cumulative_dataset_size)
        return sizes

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
