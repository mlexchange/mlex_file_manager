import base64, io
from functools import reduce

import glob
import os 
import pathlib
from PIL import Image

from file_manager.dataset.dataset import Dataset

# List of allowed and not allowed formats
FORMATS = ['**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.tif', '**/*.tiff']
NOT_ALLOWED_FORMATS = ['**/__pycache__/**', '**/.*', 'cache/', 'cache/**/', 'cache/**', 
                       'tiled_local_copy/', '**/tiled_local_copy/**', '**/tiled_local_copy/**/',
                       'mlexchange_store/**/', 'mlexchange_store/**',
                       'labelmaker_outputs/**/', 'labelmaker_outputs/**']


class LocalDataset(Dataset):
    def __init__(self, uri, type='file', **kwargs):
        '''
        Definition of a local data set
        '''
        super().__init__(uri, type)
        pass

    def read_data(self, export='base64', resize=True):
        '''
        Read data set
        Returns:
            Base64/PIL image
            Dataset URI
        '''
        filename = self.uri
        img = Image.open(filename)
        if export == 'pillow':
            return img, self.uri
        if resize:
            img.thumbnail((200,200), Image.LANCZOS)
        rawBytes = io.BytesIO()
        img.save(rawBytes, "JPEG")
        rawBytes.seek(0)        # return to the start of the file
        img = base64.b64encode(rawBytes.read())
        return 'data:image/jpeg;base64,'+img.decode("utf-8"), self.uri
    
    @staticmethod
    def filepaths_from_directory(directory, formats=FORMATS, sort=True, recursive=True):
        '''
        Retrieve a list of filepaths from a given directory
        Args:
            directory:      Directory from which datapaths will be retrieved according to formats
            formats:        List of file formats/extensions of interest, defaults to FORMATS
            sort:           Sort output list of filepaths, defaults to True
            recursive:      Recursive search [T/F]
        Returns:
            paths:          List of filepaths in directory
        '''
        if type(formats) == str:    # If a single format was selected, adapt to list
            formats = [formats]
        # Find paths that match the format of interest
        all_paths = list(reduce(lambda list1, list2: list1 + list2, \
                            (glob.glob(str(directory)+'/'+t, recursive=recursive) for t in formats)))
        # Find paths that match the not allowed file/directory formats
        not_allowed_paths = list(reduce(lambda list1, list2: list1 + list2, \
                            (glob.glob(str(directory)+'/'+t, recursive=recursive) for t in NOT_ALLOWED_FORMATS)))
        # Remove not allowed filepaths from filepaths of interest
        paths = list(set(all_paths) - set(not_allowed_paths))
        if sort:
            paths.sort()
        return paths