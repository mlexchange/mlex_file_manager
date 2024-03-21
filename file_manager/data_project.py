import bisect
import hashlib
import os
from collections import defaultdict
from datetime import datetime

import numpy as np
import requests

from file_manager.dataset.file_dataset import FileDataset
from file_manager.dataset.tiled_dataset import TiledDataset


class DataProject:
    def __init__(
        self,
        root_uri,
        data_type,
        api_key=None,
        datasets=[],
        project_id=None,
    ):
        """
        Definition of a DataProject
        Args:
            root_uri:           Root URI
            data_type:          Data type
            api_key:            API key
            datasets:           List of datasets
            project_id:         Project ID
        """
        self.root_uri = root_uri
        self.api_key = api_key
        self.datasets = datasets
        self.project_id = project_id
        self.data_type = data_type
        pass

    def to_dict(self):
        """
        Convert to dictionary
        Returns:
            Dictionary
        """
        return {
            "root_uri": self.root_uri,
            "api_key": self.api_key,
            "datasets": [dataset.to_dict() for dataset in self.datasets],
            "project_id": self.project_id,
            "data_type": self.data_type,
        }

    @classmethod
    def from_dict(cls, data_project_dict):
        """
        Create a new instance from dictionary
        Args:
            data_project_dict:           Dictionary
        Returns:
            New instance
        """
        return cls(
            data_project_dict["root_uri"],
            data_project_dict["data_type"],
            api_key=data_project_dict["api_key"],
            datasets=[
                (
                    FileDataset.from_dict(dataset)
                    if data_project_dict["data_type"] == "file"
                    else TiledDataset.from_dict(dataset)
                )
                for dataset in data_project_dict["datasets"]
            ],
            project_id=data_project_dict["project_id"],
        )

    def read_datasets(self, indices, export="base64", resize=True, log=False):
        """
        Get datasets at specific indices
        Args:
            indices:        List of indices to retrieve
            export:         Export format of the data
            resize:         Resize image to 200x200, defaults to True
            log:            Take logarithm of the data, defaults to False
        Returns:
            List of datasets
        """
        sorted_indices = np.argsort(indices)
        sorted_list = np.array(indices)[sorted_indices]

        cumulative_counts = [dataset.cumulative_data_count for dataset in self.datasets]
        dataset_indices = defaultdict(list)

        for index in sorted_list:
            new_i = bisect.bisect_right(
                [cumulative_count for cumulative_count in cumulative_counts], index
            )
            image_index = index - (cumulative_counts[new_i - 1] if new_i > 0 else 0)
            dataset_indices[new_i].append(image_index)

        images = []
        uris = []
        for dataset_index, image_indices in dataset_indices.items():
            batch_images, batch_uris = self.datasets[dataset_index].read_data(
                self.root_uri,
                image_indices,
                export=export,
                resize=resize,
                log=log,
                api_key=self.api_key,
            )
            images.extend(batch_images)
            uris.extend(batch_uris)

        return [images[i] for i in sorted_indices], [uris[i] for i in sorted_indices]

    def browse_data(
        self,
        sub_uri_template,
        selected_sub_uris=[""],
    ):
        """
        Browse data according to browse format and data type
        Args:
            sub_uri_template:       Sub URI template
            selected_sub_uris:      List of selected sub URIs
        Returns:
            data:               Retrieve Dataset according to data_type and browse format
        """
        if self.data_type == "tiled":
            uris, cumulative_data_counts = TiledDataset.browse_data(
                self.root_uri,
                self.api_key,
                sub_uri_template=sub_uri_template,
                selected_sub_uris=selected_sub_uris,
            )
            data = [
                TiledDataset(uri, cum_data_count)
                for uri, cum_data_count in zip(uris, cumulative_data_counts)
            ]
        else:
            # Add variations of the file extensions
            if sub_uri_template == "**/*.jpg":
                sub_uri_template = ["**/*.jpg", "**/*.jpeg"]
            elif sub_uri_template == "**/*.tif":
                sub_uri_template = ["**/*.tif", "**/*.tiff"]
            uris, cumulative_data_counts, filenames_per_uri = (
                FileDataset.filepaths_from_directory(
                    self.root_uri,
                    sub_uri_template,
                    selected_sub_uris=selected_sub_uris,
                )
            )
            data = [
                FileDataset(uri, cum_data_count, filenames=filenames)
                for uri, cum_data_count, filenames in zip(
                    uris, cumulative_data_counts, filenames_per_uri
                )
            ]
        return data

    @staticmethod
    def get_event_id(splash_uri):
        """
        Post a tagging event in splash-ml
        Args:
            splash_uri:         URI to splash-ml service
        Returns:
            event_uid:          UID of tagging event
        """
        event_uid = requests.post(
            f"{splash_uri}/events",  # Post new tagging event
            json={"tagger_id": "labelmaker", "run_time": str(datetime.utcnow())},
        ).json()["uid"]
        return event_uid

    @staticmethod
    def hash_tiled_uri(uri, hash_function="sha256"):
        """
        Hash a tiled URI
        Args:
            uri:            URI to hash
            hash_function:  Hash function to use
        Returns:
            Hashed URI
        """
        return hashlib.new(hash_function, uri.encode(("utf-8"))).hexdigest()

    def check_if_data_downloaded(self, indexes):
        prev_data_count = 0
        for dataset in self.datasets:
            cum_data_count = dataset.cumulative_data_count

            # Find the start and end of the subset
            start_index = bisect.bisect_left(indexes, prev_data_count)
            end_index = bisect.bisect_right(indexes, cum_data_count)

            # Get the subset of indexes within the range
            subset = indexes[start_index:end_index]
            tiled_uris = dataset.get_tiled_uris(self.root_uri, subset)
            for uri in tiled_uris:
                hashed_uri = self.hash_tiled_uri(uri)
                file_path = os.path.join("data/tiled_local_copy", hashed_uri + ".tif")
                if os.path.isfile(file_path):
                    indexes.remove(subset[tiled_uris.index(uri)])
        return indexes

    def tiled_to_local_project(self, indexes=None):
        """
        Convert a tiled data project to a local project while saving each dataset to filesystem
        Args:
            pattern:        Pattern to replace in project_id to avoid errors in filesystem
            indexes:        List of indices to download
        """
        filtered_indexes = self.check_if_data_downloaded(indexes)
        if len(filtered_indexes) > 0:
            data_contents, data_uris = self.read_datasets(
                filtered_indexes, export="pillow", resize=False, log=False
            )
            for data_content, data_uri in zip(data_contents, data_uris):
                filename = self.hash_tiled_uri(data_uri)
                data_content.save(f"data/tiled_local_copy/{filename}.tif")
        pass
