# MLExchange File Manager

Simple data management system with [Dash UI](https://dash.plotly.com) and [Tiled](https://blueskyproject.io/tiled/).

## Running simple example with [Docker](https://docs.docker.com/engine/install/)

1. Clone this repository:
    ```
    https://github.com/mlexchange/mlex_file_manager
    ```

2. Within the ``mlex_file_manager`` directory, run the following command:
    ```
    docker-compose up --build
    ```
3. Access the sample application at [localhost:8050](localhost:8050)

## Ingest data with MLExchange File Manager
The MLExchange File Manager supports data access through:

1. Loading data from file system: You can access image data located at the ```data``` folder in the main directory. Currently, the supported formats are: PNG, JPG/JPEG, and TIF/TIFF.

2. Loading data from [Tiled](https://blueskyproject.io/tiled/): Alternatively, you can access data through Tiled by providing a ```tiled_server_uri``` in the frontend of your application and the ```TILED_KEY``` associated with this server as an environment variable.

3. Browse directories or Tiled nodes and **IMPORT** the selected files.

4. [Optional] Upload data with the **Drag and Drop** option in the frontend.
Upload either a single file or a zip file (files) through drag and drop.
User can then browse the newly added files/folder in the path table.

## How to set up MLExchange File Manager in your application

1. Define your ploty app with a [long_callback_manager](https://dash.plotly.com/long-callbacks)
    ```
    app = dash.Dash(__name__,
                    long_callback_manager=long_callback_manager)
    ```

2. Define your file explorer, initialize its callbacks, and set up the upload data path considering the following parameters:

    - data_folder_root:       [str] Root folder to data directory for local loading
    - upload_folder_root:     [str] Root folder to upload directory
    - splash_uri:             [str] URI to splash-ml service
    - max_file_size:          [int] Maximum file size for uploaded data, defaults to 60000
    - open_explorer:          [bool] Open/close the file explorer at start up
    - api_key:                [str] Tiled API key

    An example code to set this up is shown bellow:
    ```
    # Create the file manager dash object
    dash_file_explorer = FileManager(data_folder_root,
                                     upload_folder_root,
                                     splash_uri,
                                     max_file_size
                                     open_explorer,
                                     api_key)
    # Init callbacks
    dash_file_explorer.init_callbacks(app)
    # Configure upload folder
    du.configure_upload(app, upload_folder_root, use_upload_id=False)
    ```

3. Incorporate the following dash components to your callbacks to load the data:

    - ```Input({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data')```

        List of selected data sets, e.g. [dataset1, dataset2], where dataset1 can be a LocalDataset or TiledDataset.
    - [Optional] ```Output({'base_id': 'file-manager', 'name': 'confirm-update-data'}, 'data'),```

        Bool flag that indicates if the dataset can be updated. If this flag is set to *False*, the *CLEAR DATA* button in the frontend application will not allow importing new data until the flag is set to *True*. This prevents users from accidently clearing the data without saving their results.

4. Accessing data:

    ```
    from file_manager.data_project import DataProject

    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    ```

    In the previous example, ```file_paths``` correspond to the dictionary stored in ```{'base_id': 'file-manager', 'name': 'docker-file-paths'}```. Once the data is loaded in the corresponding object, we can access the 10th (index=9) element of this project by using:

    ```
    base64_image, image_uri = data_project.data[9].read_data(export='base64',
                                                             resize=True)
    ```

    The parameters of *read_data* are described as follows:
        - export: 'base64' or 'pillow', default 'base64'
        - resize: True/False, defaults to True. When True, the image is resized to 200x200 pixels approximately while keeping the aspect ratio of the original image

## Copyright

MLExchange Copyright (c) 2024, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy). All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

(1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

(2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

(3) Neither the name of the University of California, Lawrence Berkeley National Laboratory, U.S. Dept. of Energy nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
