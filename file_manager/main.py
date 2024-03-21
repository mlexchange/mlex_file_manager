import os, pathlib, pickle, zipfile
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash_daq as daq
import time

from file_manager.dash_file_explorer import create_file_explorer
from file_manager.data_project import DataProject


class FileManager():
    def __init__(self, data_folder_root, upload_folder_root, splash_uri='http://splash:80/api/v0', 
                 max_file_size=60000, open_explorer=True, api_key=None, default_tiled_uri=''):
        '''
        FileManager creates a dash file explorer that supports: (1) local file reading, and (2)
        data access through Tiled
        Args:
            data_folder_root:       [str] Root folder to data directory for local loading
            upload_folder_root:     [str] Root folder to upload directory
            splash_uri:             [str] URI to splash-ml service
            max_file_size:          [int] Maximum file size for uploaded data, defaults to 60000
            open_explorer:          [bool] Open/close the file explorer at start up
            api_key:                [str] Tiled API key
            default_tiled_uri:      [str] Default Tiled URI to be displayed in file manager
        '''
        self.data_folder_root = data_folder_root
        self.upload_folder_root = upload_folder_root
        self.max_file_size = max_file_size
        self.splash_uri = splash_uri
        self.api_key = api_key
        self.manager_filename = f'{self.data_folder_root}/.file_manager_vars.pkl'
        # Definition of the dash components for file manager
        self.file_explorer = html.Div(
            [
                dbc.Row([
                    dbc.Col(
                        dbc.Button(
                                'Toggle Explorer',
                                id={'base_id': 'file-manager', 'name': 'collapse-button'},
                                n_clicks=0,
                                style={'width': '100%', 
                                       'color': 'white', 
                                       'background-color': '#007681',
                                       'border-color': '#007681'}
                            ),
                    ),
                    dbc.Col(
                        dbc.Button(
                            'Refresh Project',
                            id={'base_id': 'file-manager', 'name': 'refresh-data'},
                            color='secondary',
                            n_clicks=0,
                            style={'width': '100%', 
                                   'color': 'white', 
                                   'background-color': '#007681',
                                   'border-color': '#007681'}
                        ),
                    ),
                    dbc.Col(
                        dbc.Button(
                            'Clear Images',
                            id={'base_id': 'file-manager', 'name': 'clear-data'},
                            color='danger',
                            n_clicks=0,
                            style={'width': '100%'}
                        ),
                    ),
                    dcc.Loading(
                        id={'base_id': 'file-manager', 'name': 'loading-cube'},
                        type="cube",
                        children=[
                            dbc.Modal(
                                children=[
                                    dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                    dbc.ModalBody(children="Could not connect to Tiled"),
                                    ], 
                                id={'base_id': 'file-manager', 'name': 'tiled-error'},
                                is_open=False,
                                style = {'color': 'red'}
                            )],
                        style={'background-color': 'transparent'},
                        fullscreen=True
                        ),
                ], className="g-0", justify="center"),
                dbc.Row(
                    daq.BooleanSwitch(
                        id={'base_id': 'file-manager', 'name': 'log-toggle'},
                        label="Log",
                        labelPosition="top"
                    ),
                ),
                dbc.Collapse(
                    create_file_explorer(max_file_size, default_tiled_uri),
                    id={'base_id': 'file-manager', 'name': 'collapse-explorer'},
                    is_open=open_explorer,
                ),
            ]
        )
        pass
    
    def init_callbacks(self, app):
        '''
        Definition of the callbacks to support the functionality of the file manager components
        Args:
            app:        Dash app that contains a file manager
        '''
        app.callback(
            Output({'base_id': 'file-manager', 'name': 'collapse-explorer'}, 'is_open'),
            [Input({'base_id': 'file-manager', 'name': 'collapse-button'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'import-dir'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'refresh-data'}, 'n_clicks'),
             State({'base_id': 'file-manager', 'name': 'collapse-explorer'}, 'is_open')]
        )(self._toggle_collapse)

        app.callback(
            Output({'base_id': 'file-manager', 'name': 'upload-data'}, 'data'),
            [Input({'base_id': 'file-manager', 'name': 'dash-uploader'}, 'isCompleted'),
             State({'base_id': 'file-manager', 'name': 'dash-uploader'}, 'fileNames')],
             prevent_initial_call=True
        )(self._upload_zip)

        app.long_callback(
            Output({'base_id': 'file-manager', 'name': 'files-table'}, 'data'),
            [Input({'base_id': 'file-manager', 'name': 'browse-format'}, 'value'),
             Input({'base_id': 'file-manager', 'name': 'upload-data'}, 'data'),
             State({'base_id': 'file-manager', 'name': 'tabs'}, 'value')]
        )(self._load_table)
        pass

        app.long_callback(
            [Output({'base_id': 'file-manager', 'name': 'files-table'}, 'selected_rows'),
             Output({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data'),
             Output({'base_id': 'file-manager', 'name': 'tiled-error'}, 'is_open'),
             Output({'base_id': 'file-manager', 'name': 'tabs'}, 'value'),
             Output({'base_id': 'file-manager', 'name': 'project-id'}, 'data'),
            ],
            [Input({'base_id': 'file-manager', 'name': 'import-dir'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'refresh-data'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'clear-data'}, 'n_clicks'),
             State({'base_id': 'file-manager', 'name': 'tabs'}, 'value'),
             State({'base_id': 'file-manager', 'name': 'confirm-update-data'}, 'data'),
             State({'base_id': 'file-manager', 'name': 'files-table'}, 'selected_rows'),
             State({'base_id': 'file-manager', 'name': 'tiled-uri'}, 'value'),
             State({'base_id': 'file-manager', 'name': 'files-table'}, 'data'),
             State({'base_id': 'file-manager', 'name': 'import-format'}, 'value')]
        )(self._load_dataset)
        pass

    @staticmethod
    def _toggle_collapse(collapse_n_clicks, import_n_clicks, refresh_n_clicks, is_open):
        '''
        Collapse the file manager once a data set has been selected
        Args:
            collapse_n_clicks:  Number of clicks in collapse button
            import_n_clicks:    Number of clicks in import button
            refresh_n_clicks:   Number of clicks on refresh data button
            is_open:            Bool variable indicating if file manager is collapsed or not
        Returns:
            is_open:            Updated state of is_open
        '''
        changed_id = dash.callback_context.triggered[0]['prop_id']
        if 'refresh-data' in changed_id or 'import' in changed_id:
            return False
        elif collapse_n_clicks:
            return not is_open
        return is_open

    def _upload_zip(self, iscompleted, upload_filename):
        '''
        Unzip uploaded files and save them at upload folder root
        Args:
            iscompleted:            Flag indicating if the upload + unzip are complete
            upload_filenames:       List of filenames that were uploaded
        Returns:
            flag:                   Bool indicating if the uploading process is completed
        '''
        if not iscompleted:
            return False
        if upload_filename is not None:
            path_to_zip_file = pathlib.Path(self.upload_folder_root) / upload_filename[0]
            if upload_filename[0].split('.')[-1] == 'zip':
                zip_ref = zipfile.ZipFile(path_to_zip_file)                 # create zipfile object
                path_to_folder = pathlib.Path(self.upload_folder_root) / \
                                 upload_filename[0].split('.')[-2]
                if (upload_filename[0].split('.')[-2] + '/') in zip_ref.namelist():
                    zip_ref.extractall(pathlib.Path(self.upload_folder_root))  # extract file to dir
                else:
                    zip_ref.extractall(path_to_folder)
                zip_ref.close()     # close file
                os.remove(path_to_zip_file)
        return True
    
    def _load_table(self, browse_format, uploaded_data, tab_value):
        '''
        This callback updates the content of the file table
        Args:
            browse_format:      File extension to browse
            uploaded_data:      Flag that indicates if new data has been uploaded
            tab_value:          Tab indicating data access method (filesystem/tiled)
        Returns:
            table_data:         Updated table data according to browsing selection
        '''
        data_project = DataProject(data=[])
        if tab_value != 'tiled':
            browse_data = data_project.browse_data(tab_value, browse_format,
                                                   tiled_uri = None,
                                                   dir_path=self.data_folder_root,
                                                   api_key=None,
                                                   recursive=False)
        else:
            browse_data = []
        return DataProject(data=browse_data).get_table_dict()

    def _load_dataset(self, import_n_clicks, refresh_data, clear_data_n_clicks, tab_value,
                      update_data, rows, tiled_uri, files_table, import_format):
        '''
        This callback manages the actions of file manager
        Args:
            browse_format:          File extension to browse
            import_n_clicks:        Number of clicks on import button
            refresh_data:           Number of clicks on refresh data button
            uploaded_data:          Flag that indicates if new data has been uploaded
            clear_data_n_clicks:    Number of clicks on clear data button
            tab_value:              Tab indicating data access method (filesystem/tiled)
            update_data:            Flag that indicates if the dataset can be updated
            rows:                   Selected rows in table of files/directories/nodes
            tiled_uri:              Tiled URI for data access
            files_table:            Current values within the table of files/directories/nodes
            import_format:          File extension to import
        Returns: 
            table_data_rows:        Updated selection of rows in table data
            selected_files:         List of selected data sets for later analysis
            tiled_warning_modal:    Open warning indicating that the connection to tiled failed
            tab_value:              Tab indicating data access method (filesystem/tiled)
            project_id:             Project ID to track the project of interest
        '''
        start = time.time()
        changed_id = dash.callback_context.triggered[0]['prop_id']
        data_project = DataProject(data=[])
        project = dash.no_update
        # prevent update according to update_data flag
        if changed_id in ['{"base_id":"file-manager","name":"clear-data"}.n_clicks',
                          '{"base_id":"file-manager","name":"refresh-data"}.n_clicks',
                          '{"base_id": "file-manager", "name": "import-dir"}.n_clicks'] and not update_data:
            raise PreventUpdate
        elif 'clear-data' in changed_id:
            return dash.no_update, [], dash.no_update, dash.no_update, dash.no_update
        elif 'refresh-data' in changed_id and os.path.exists(self.manager_filename):
            with open(self.manager_filename, 'rb') as file:
                contents = pickle.load(file)
            data_project_dict = contents['data_project']
            data_project.init_from_dict(data_project_dict)
            project = contents['project_id']
            row_indx, tab_value = self._match_table_row(data_project, files_table, tab_value)
            print(f'Done after {time.time() - start} with project {project}')
            return row_indx, data_project_dict, dash.no_update, tab_value, project

        if tab_value != 'tiled' and bool(rows):
            for row in rows:
                selected_row = files_table[row]['uri']
                data_project.data += data_project.browse_data(tab_value, import_format, \
                                                            tiled_uri = selected_row,
                                                            dir_path = selected_row,
                                                            api_key=self.api_key)
                project = selected_row
        else:
            project = ''
            tiled_uris = tiled_uri.split(',')
            for tiled_uri in tiled_uris:
                data_project.data += data_project.browse_data(tab_value, import_format, \
                                                            tiled_uri = tiled_uri,
                                                            api_key=self.api_key)
                project += f'{tiled_uri},'
            project = project[:-1]

        if len(data_project.data)>0:
            with open(self.manager_filename, 'wb') as file:
                pickle.dump({'data_project': data_project.get_dict(),
                                'project_id': project}, file)
        selected_data = data_project.get_dict()
        print(f'Done after {time.time() - start} with project {project}')
        return dash.no_update, selected_data, dash.no_update, dash.no_update, project
    
    def _match_table_row(self, data_project, files_table, tab_value, browse_format='**/'):
        '''
        This callback matches the selected row in the table with the data set that is being loaded (Refresh)
        Args:
            data_project:       DataProject object
            files_table:        Current values within the table of files/directories/nodes
            tab_value:          Tab indicating data access method (filesystem/tiled)
            browse_format:      File extension to browse
        Returns:
            row_indx:           Index of the selected row in the table
            tab_value:          Tab indicating data access method (filesystem/tiled)
        '''
        first_uri = data_project.data[0].uri
        row_indx = [next((indx for indx, row in enumerate(files_table) if row['uri'] in first_uri), None)]
        if row_indx is [None]:
            if tab_value=='tiled':
                tab_value = 'file'
                tiled_uri = None
            else:
                tab_value = 'tiled'
                tiled_uri = first_uri.split('/api/v1')[0]
            files_table = data_project.browse_data(tab_value, browse_format, \
                                                   tiled_uri = tiled_uri,
                                                   dir_path=self.data_folder_root,
                                                   api_key=self.api_key,
                                                   recursive=False)
            row_indx = [next((indx for indx, row in enumerate(files_table) if row.uri in first_uri), None)]
        return row_indx, tab_value