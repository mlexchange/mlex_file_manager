from datetime import datetime
from functools import partial
from typing import List
import time
import re
import pathlib
import uuid
import pandas as pd
import concurrent.futures

from PIL import Image
import requests
from uuid import uuid4

from file_manager.dataset.local_dataset import LocalDataset
from file_manager.dataset.tiled_dataset import TiledDataset


class DataProject:
    def __init__(self, data: List = [], project_id = None):
        '''
        Definition of a DataProject
        Args:
            data:       List of data sets within the project
            project_id: Project ID to track the project of interest
        '''
        self.data = data
        self.project_id = project_id
        pass

    def init_from_dict(self, data: List, api_key=None):
        '''
        Initialize the object from a dictionary
        '''
        self.data = []
        for item in data:
            if item['type']=='tiled':
                if 'api_key' not in item:
                    item['api_key'] = api_key
                self.data.append(TiledDataset(**item))
            else:
                self.data.append(LocalDataset(**item))
        pass
    
    def init_from_splash(self, splash_uri, project_id=None, api_key=None):
        '''
        Initialize the object from splash
        '''
        datasets = []
        num_elem = 5000
        indx = 0
        while num_elem==5000:
            elem = requests.post(f'{splash_uri}?page%5Boffset%5D={indx}&page%5Blimit%5D=5000',
                                 json={'project': project_id}).json()
            num_elem = len(elem)
            datasets += elem
            indx += 5000
        self.init_from_dict(datasets, api_key)
        pass
        
    @staticmethod
    def browse_data(data_type, browse_format, dir_path=None, tiled_uri=None, api_key=None, 
                    recursive=True):
        '''
        Browse data according to browse format and data type
        Args:
            data_type:          Tiled or local
            browse_format:      File format to retrieve during this process
            dir_path:           Directory path if data_type is local
            tiled_uri:          Tiled URI if data_type is tiled
            api_key:            Tiled API key
            recursive:          [Bool] activate recursive search
        Returns:
            data:               Retrieve Dataset according to data_type and browse format
        '''
        if data_type == 'tiled':
            uris = TiledDataset.browse_data(tiled_uri, browse_format, api_key=api_key, tiled_uris=[],
                                            recursive=recursive)
            data = [TiledDataset(uri=item, api_key=api_key) for item in uris]
        else:
            if browse_format=='*':
                uris = LocalDataset.filepaths_from_directory(dir_path)
            else:
                if browse_format == '**/*.jpg':             # Add variations of the file extensions
                    browse_format = ['**/*.jpg', '**/*.jpeg']
                elif browse_format == '**/*.tif':
                    browse_format = ['**/*.tif', '**/*.tiff']
                # Recursively call the method if a subdirectory is encountered
                uris = LocalDataset.filepaths_from_directory(dir_path, browse_format, 
                                                             recursive=recursive)
            data = [LocalDataset(uri=str(item)) for item in uris]
        return data
    
    def get_dict(self):
        '''
        Retrieve the dictionary from the object
        '''
        data_project_dict = [dataset.__dict__ for dataset in self.data]
        return data_project_dict
    
    def get_table_dict(self):
        '''
        Retrieve a curated dictionary for the dash table without tags due to imcompatibility with 
        dash table and a list of items in a cell
        '''
        data_table_dict = [{"uri": dataset.uri, "type": dataset.type} for dataset in self.data]
        return data_table_dict
    
    def get_event_id(self, splash_uri):
        '''
        Post a tagging event in splash-ml
        Args:
            splash_uri:         URI to splash-ml service
        Returns:
            event_uid:          UID of tagging event
        '''
        event_uid = requests.post(f'{splash_uri}/events',               # Post new tagging event
                                  json={'tagger_id': 'labelmaker',
                                        'run_time': str(datetime.utcnow())}).json()['uid']
        return event_uid
    
    @staticmethod
    def save_tiled_locally(dataset, filename, project_id):
        img, _ = dataset.read_data(export='pillow', resize=False)       # Get data
        img.save(filename)                                              # Save data to new path
        return LocalDataset(filename, project=project_id)
    
    def tiled_to_local_project(self, subset=None, pattern = r'[/\\?%*:|"<>]'):
        '''
        Convert a tiled data project to a local project while saving each dataset to filesystem
        Args:
            pattern:        Pattern to replace in project_id to avoid errors in filesystem
            subset:         List of indices to subset the data project to download
        Returns:
            local_data_project
        '''
        list_project_id = self.project_id.split(',')
        data_info = pd.DataFrame()
        start_indx = 0
        for unit_project_id in list_project_id:
            unit_uris = []
            unit_indx = []
            for indx, dataset in enumerate(self.data):
                if dataset.uri.startswith(unit_project_id):
                    unit_uris.append(dataset.uri)
                    unit_indx.append(indx)
            cleaned_project_id = re.sub(pattern, '_', unit_project_id)
            local_path = pathlib.Path(f'data/tiled_local_copy/{cleaned_project_id}')

            # Check if the all the data within  is already saved locally
            if local_path.exists() and len(unit_uris)==len(list(local_path.glob('*.tif'))):
                unit_data_info = pd.read_parquet(f'{local_path}/data_info.parquet', engine='pyarrow')
            else:
                # Get subset of interest if provided
                if subset is not None:
                    filtered_subset = [num-start_indx for num in subset if start_indx <= num < start_indx+len(unit_uris)]
                    unit_uris = [unit_uris[i] for i in filtered_subset]
                    unit_indx = [unit_indx[i] for i in filtered_subset]
                
                # Check if the some data points are already saved locally
                if local_path.exists() and len(unit_uris)>0:
                    partial_data_info = pd.read_parquet(f'{local_path}/data_info.parquet', engine='pyarrow')
                    partial_local_uris = partial_data_info['uri'].tolist()
                    filtered = [(uri, indx) for uri, indx in zip(unit_uris, unit_indx) if uri not in partial_local_uris]
                    if filtered:
                        unit_uris, unit_indx = zip(*filtered)
                    else:
                        continue
                else:
                    partial_data_info = None

                # Generate unique ids for each data point
                uid_list = []
                for ii in range(len(unit_uris)):
                    uid_list.append(str(uuid.uuid4()))
                
                # Initialize data_info dataframe
                unit_data_info = pd.DataFrame({'uri': unit_uris})
                unit_data_info['type'] = ['tiled']*len(unit_uris)
                unit_data_info['local_uri'] = [f'{local_path}/{uid}.tif' for uid in uid_list]

                # Save data locally
                local_path.mkdir(parents=True, exist_ok=True)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    local_datasets = list(executor.map(self.save_tiled_locally, 
                                                       [self.data[i] for i in unit_indx], 
                                                       list(unit_data_info['local_uri']), 
                                                       [unit_project_id]*len(unit_uris)))

                # Update data_info dataframe if it already existed
                if partial_data_info is not None:
                    unit_data_info = pd.concat([partial_data_info, unit_data_info], ignore_index=True)
                unit_data_info.to_parquet(f'{local_path}/data_info.parquet', engine='pyarrow')
            
            data_info = pd.concat([data_info, unit_data_info], ignore_index=True)
            start_indx += len(unit_uris)
        return data_info