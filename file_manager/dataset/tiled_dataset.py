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

    @staticmethod
    def _process_image(image, threshold=1):
        '''
        Process image
        Args:
            image:      PIL image
        Returns:
            PIL image
        '''
        image = np.array(image, dtype=np.float32)
        image = np.log(image+threshold)
        image = ((image - np.min(image)) / (np.max(image) - np.min(image)) * 255).astype(np.uint8)
        return Image.fromarray(image)
    
    @staticmethod
    def _get_response(tiled_uri, expected_shape, resize, max_tries):
        '''
        Get response from tiled URI
        Args:
            tiled_uri:          Tiled URI from which data should be retrieved
            expected_shape:     Expected shape of the data
            resize:             Resize image to 200x200, defaults to True
            max_tries:          Maximum number of tries to retrieve data, defaults to 5
        Returns:
            Response content
        '''
        status_code = 502
        trials = 0
        while status_code != 200 and trials < max_tries:
            if len(expected_shape) == 3:
                response = requests.get(f'{tiled_uri},0,::5,::5&format=png') if resize \
                    else requests.get(f'{tiled_uri},0,:,:&format=png')
            else:
                response = requests.get(f'{tiled_uri},::5,::5&format=png') if resize \
                    else requests.get(f'{tiled_uri},:,:&format=png')
            status_code = response.status_code
            trials += 1
            if status_code != 200:
                print(response.content)
        return response.content
        
    def read_data(self, export='base64', resize=True, log=False, max_tries=5):
        '''
        Read data set
        Args:
            export:             Export format, defaults to base64
            resize:             Resize image to 200x200, defaults to True
            log:                Apply log(1+x) to the image, defaults to False
            max_tries:          Maximum number of tries to retrieve data, defaults to 5
        Returns:
            Base64/PIL image
            Dataset URI
        '''
        tiled_uri, metadata = self.uri.split('&expected_shape=')
        expected_shape, dtype = metadata.split('&dtype=')
        expected_shape = np.array(list(map(int, expected_shape.split('%2C'))))

        if len(expected_shape) == 3 and expected_shape[0] in [1,3,4]:
            expected_shape = expected_shape[[1,2,0]]
        elif len(expected_shape) != 2 or expected_shape[-1] not in [1,3,4]:
            raise RuntimeError(f"Not supported type of data. Tiled uri: {tiled_uri} and data dimension {expected_shape}")

        contents = self._get_response(tiled_uri, expected_shape, resize, max_tries)

        if export == 'pillow':
            image = Image.open(io.BytesIO(contents))
            if log:
                image = self._process_image(image)
            return (image.crop((0, 1, *image.size)), self.uri) if resize else (image, self.uri)

        if log:
            image = self._process_image(Image.open(io.BytesIO(contents)))
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            contents = buffered.getvalue()

        contents_base64 = base64.b64encode(contents).decode('utf-8')
        return f'data:image/jpeg;base64,{contents_base64}', self.uri

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