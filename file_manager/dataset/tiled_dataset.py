import base64, io, time
import numpy as np
from PIL import Image
from requests.auth import HTTPBasicAuth
import requests

from tiled.client import from_uri, show_logs
from tiled.client.node import Node

from file_manager.dataset.dataset import Dataset

class TiledDataset(Dataset):
    def __init__(self, uri, type='tiled', api_key=None, **kwargs):
        '''
        Definition of a tiled data set
        '''
        super().__init__(uri, type)
        self.api_key=api_key
        pass

    def read_data(self, export='base64', resize=True, threshold=1100):
        '''
        Read data set
        Returns:
            Base64/PIL image
            Dataset URI
        '''
        main_uri = self.uri.split('/api')[0]
        if self.api_key:
            client = from_uri(main_uri, api_key=self.api_key)
        else:
            client = from_uri(main_uri)
        # Retrieve tiled_uri and expected shape
        tiled_uri, metadata = self.uri.split('&expected_shape=')
        expected_shape, dtype = metadata.split('&dtype=')
        expected_shape = np.array(list(map(int, expected_shape.split('%2C'))))
        # Validate image data
        if len(expected_shape)==3:
            if expected_shape[0] in [1,3,4]:          # channels first
                expected_shape = expected_shape[[1,2,0]]
            elif expected_shape[-1] not in [1,3,4]:   # channels last
                raise RuntimeError(f"Not supported type of data. Tiled uri: {tiled_uri} and data \
                                    dimension {expected_shape}")
        elif 2>len(expected_shape) or len(expected_shape)>3:
            raise RuntimeError(f"Not supported type of data. Tiled uri: {tiled_uri} and data \
                               dimension {expected_shape}")
        status_code = 502
        trials = 0
        # Resize if needed
        if resize:
            # start = time.time()
            while status_code!=200 and trials<5:
                if len(expected_shape)==3:
                    response = client.context.http_client.get(f'{tiled_uri},0,::10,::10&format=png')
                else:
                    response = client.context.http_client.get(f'{tiled_uri},::10,::10&format=png')
                status_code = response.status_code
                trials =+ 1
                if status_code!= 200:
                    print(response.content)
            contents = response.content
            # print(f'Response alone: {time.time()-start}', flush=True)
        else:
            while status_code!=200 and trials<5:
                response = client.context.http_client.get(f'{tiled_uri},0,:,:&format=png')
                status_code = response.status_code
                trials =+ 1
            contents = response.content
        if status_code!= 200:
            pass
        base64_data = base64.b64encode(contents).decode('utf-8')
        return f'data:image/jpeg;base64,{base64_data}', self.uri

    @staticmethod
    def browse_data(tiled_uri, browse_format, tiled_uris=[], tiled_client=None, api_key=None, 
                    recursive=False):
        '''
        Retrieve a list of nodes from tiled URI
        Args:
            tiled_uri:          Tiled URI from which data should be retrieved
            browse_format:      List of file formats/extensions of interest, defaults to FORMATS
            tiled_uris:         List of current tiled URIs, which is used when the method is run
                                recursively, defaults to []
            tiled_client:       Current tiled client, which is used when the method is run
                                recursively, defaults to None
            api_key:            Tiled API key
        Returns:
            tiled_uris:         List of tiled URIs found in tiled client
        '''
        if not tiled_client:
            metadata_tiled_uri, _ = TiledDataset.array_to_metadata_uri(tiled_uri)
            if api_key:
                tiled_client = from_uri(metadata_tiled_uri, api_key=api_key)
            else:
                tiled_client = from_uri(metadata_tiled_uri)
        if isinstance(tiled_client, Node):
            nodes = list(tiled_client)
            for node in nodes:
                mod_tiled_uri = TiledDataset.update_tiled_uri(tiled_uri, node)
                if browse_format != '**/' and recursive:
                    node_info = tiled_client[node]
                    dtype = node_info.dtype
                    data_shape = node_info.shape
                    num_imgs = data_shape[0]
                    expected_shape = list(map(str, data_shape[1:]))
                    expected_shape = '%2C'.join(expected_shape)
                    tiled_uris = tiled_uris + [f"{mod_tiled_uri}?slice={i}&expected_shape={expected_shape}&dtype={dtype}" for i in range(num_imgs)]
                else:
                    tiled_uris.append(mod_tiled_uri)
        else:
            if browse_format != '**/' and recursive:
                data_shape = tiled_client.shape
                dtype = tiled_client.dtype
                num_imgs = int(data_shape[0])
                expected_shape = list(map(str, data_shape[1:]))
                expected_shape = '%2C'.join(expected_shape)
                tiled_uris = tiled_uris + [f"{tiled_uri}?slice={i}&expected_shape={expected_shape}&dtype={dtype}" for i in range(num_imgs)]
            else:
                tiled_uris.append(tiled_uri)
        return tiled_uris
    
    @staticmethod
    def update_tiled_uri(tiled_uri, node):
        '''
        Update tiled URI to reflect nodes
        '''
        if '/api/v1/array/full' in tiled_uri:
            return f'{tiled_uri}/{node}'
        elif tiled_uri[-1] == '/':
            return f'{tiled_uri}api/v1/array/full/{node}'
        else:
            return f'{tiled_uri}/api/v1/array/full/{node}'
        
    @staticmethod
    def array_to_metadata_uri(tiled_uri):
        '''
        Converts an array tiled uri to a metadata uri
        '''
        tiled_uri = tiled_uri.replace('array/full', 'metadata')
        if '?slice=' in tiled_uri:
            tiled_uri, indx = tiled_uri.split('?slice=')
            indx = int(indx)
        else:
            indx = None
        return tiled_uri, indx