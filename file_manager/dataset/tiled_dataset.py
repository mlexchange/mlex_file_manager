import base64, io
import numpy as np
from PIL import Image

from tiled.client import from_uri
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
        base_uri, indx = self.array_to_metadata_uri(self.uri)
        if self.api_key:
            tiled_client = from_uri(base_uri, api_key=self.api_key)
        else:
            tiled_client = from_uri(base_uri)
        if resize:
            if len(tiled_client.shape)==4:
                img_array = tiled_client[indx,0,::5,::5]
            else:
                img_array = tiled_client[indx,::5,::5]
        else:
            if len(tiled_client.shape)==4:
                img_array = tiled_client[indx,0]
            else:
                img_array = tiled_client[indx]
        if np.max(img_array)>255:
            img_array[img_array>threshold]=threshold
            img_array = (img_array-np.min(img_array))/(np.max(img_array)-np.min(img_array))
        img = Image.fromarray(img_array*255)
        img = img.convert("L")
        if export=='pillow':
            return img, self.uri
        rawBytes = io.BytesIO()
        img.save(rawBytes, format="JPEG")
        rawBytes.seek(0)
        img = base64.b64encode(rawBytes.read())
        return f'data:image/jpeg;base64,{img.decode("utf-8")}', self.uri

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
                    num_imgs = len(node_info)
                    tiled_uris = tiled_uris + [f"{mod_tiled_uri}?slice={i}" for i in range(num_imgs)]
                else:
                    tiled_uris.append(mod_tiled_uri)
        else:
            if browse_format != '**/' and recursive:
                num_imgs = len(tiled_client)
                tiled_uris = tiled_uris + [f"{tiled_uri}?slice={i}" for i in range(num_imgs)]
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