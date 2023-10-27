import os, pathlib, pickle, zipfile
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import time

from file_manager.dash_file_explorer import create_file_explorer
from file_manager.data_project import DataProject


class FileManager():
    def __init__(self, data_folder_root, upload_folder_root, splash_uri='http://splash:80/api/v0', 
                 max_file_size=60000, open_explorer=True, api_key=None):
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
                dbc.Collapse(
                    create_file_explorer(max_file_size),
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
            [Output({'base_id': 'file-manager', 'name': 'files-table'}, 'data'),
             Output({'base_id': 'file-manager', 'name': 'files-table'}, 'selected_rows'),
             Output({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data'),
             Output({'base_id': 'file-manager', 'name': 'tiled-error'}, 'is_open'),
             Output({'base_id': 'file-manager', 'name': 'tiled-switch'}, 'on'),
             Output({'base_id': 'file-manager', 'name': 'project-id'}, 'data'),
            ],
            [Input({'base_id': 'file-manager', 'name': 'browse-format'}, 'value'),
             Input({'base_id': 'file-manager', 'name': 'import-dir'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'refresh-data'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'upload-data'}, 'data'),
             Input({'base_id': 'file-manager', 'name': 'confirm-update-data'}, 'data'),
             Input({'base_id': 'file-manager', 'name': 'clear-data'}, 'n_clicks'),
             Input({'base_id': 'file-manager', 'name': 'tiled-switch'}, 'on'),
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
        if 'refresh-data' in changed_id:
            return False
        elif collapse_n_clicks or import_n_clicks:
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
    
    def _load_dataset(self, browse_format, import_n_clicks, refresh_data, uploaded_data, update_data, \
                      clear_data_n_clicks, tiled_on, rows, tiled_uri, files_table, import_format):
        '''
        This callback manages the actions of file manager
        Args:
            browse_format:          File extension to browse
            import_n_clicks:        Number of clicks on import button
            refresh_data:           Number of clicks on refresh data button
            uploaded_data:          Flag that indicates if new data has been uploaded
            update_data:            Flag that indicates if the dataset can be updated
            clear_data_n_clicks:    Number of clicks on clear data button
            tiled_on:               Bool indicating if tiled has been selected for data access
            rows:                   Selected rows in table of files/directories/nodes
            tiled_uri:              Tiled URI for data access
            files_table:            Current values within the table of files/directories/nodes
            import_format:          File extension to import
        Returns
            table_data:             Updated table data according to browsing selection   
            table_data_rows:        Updated selection of rows in table data
            selected_files:         List of selected data sets for later analysis
            tiled_warning_modal:    Open warning indicating that the connection to tiled failed
            tiled_on:               If connection to tiled fails, tiled_on is defaulted to False
        '''
        start = time.time()
        changed_id = dash.callback_context.triggered[0]['prop_id']
        data_project = DataProject(data=[])
        project = dash.no_update
        # prevent update according to update_data flag
        if 'import-dir' in changed_id and not update_data:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
                   dash.no_update
        elif changed_id in ['{"base_id":"file-manager","name":"clear-data"}.n_clicks',
                            '{"base_id":"file-manager","name":"refresh-data"}.n_clicks'] \
                            and not update_data:
            return dash.no_update, [], dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif 'clear-data' in changed_id:
            return dash.no_update, dash.no_update, [], dash.no_update, dash.no_update, dash.no_update
        elif 'refresh-data' in changed_id and os.path.exists(self.manager_filename):
            with open(self.manager_filename, 'rb') as file:
                contents = pickle.load(file)
            data_project_dict = contents['data_project']
            data_project.init_from_dict(data_project_dict)
            project = contents['project_id']
            table_data, row_indx, tiled_on = self._match_table_row(data_project, files_table, tiled_on)
            print(f'Done after {time.time() - start} with project {project}')
            return table_data, row_indx, data_project.get_dict(), dash.no_update, \
                tiled_on, project
        data_type = 'tiled' if tiled_on else 'file'     # Definition of the data type
        try:
            browse_data = data_project.browse_data(data_type, browse_format, \
                                                   tiled_uri = tiled_uri,
                                                   dir_path=self.data_folder_root,
                                                   api_key=self.api_key,
                                                   recursive=False)
        except Exception as e:
            print(f'Cannot connect to tiled due to {e}')
            return dash.no_update, dash.no_update, dash.no_update, True, False, dash.no_update
        if bool(rows) and 'tiled-switch' not in changed_id:
            for row in rows:
                selected_row = files_table[row]['uri']
                data_project.data += data_project.browse_data(data_type, import_format, \
                                                              tiled_uri = selected_row,
                                                              dir_path = selected_row,
                                                              api_key=self.api_key)
                project = selected_row
        if 'tiled-switch' in changed_id:
            # If the tiled selection triggered this callback, the data shown in the screen
            # should not be updated until a node (row) has been selected and imported
            selected_data = dash.no_update
        else:
            if len(data_project.data)>0:
                with open(self.manager_filename, 'wb') as file:
                    pickle.dump({'data_project': data_project.get_dict(),
                                 'project_id': project}, file)
            selected_data = data_project.get_dict()
        browse_data = DataProject(data=browse_data).get_table_dict()
        print(f'Done after {time.time() - start} with project {project}')
        return browse_data, dash.no_update, selected_data, dash.no_update, dash.no_update, project
    
    def _match_table_row(self, data_project, files_table, tiled_on, browse_format='**/'):
        first_uri = data_project.data[0].uri
        row_indx = next((indx for indx, row in enumerate(files_table) if row['uri'] in first_uri), None)
        if row_indx is None:
            if tiled_on:
                tiled_on = False
                tiled_uri = None
            else:
                tiled_on = True
                tiled_uri = first_uri.split('/api/v1')[0]
            data_type = 'tiled' if tiled_on else 'file'     # Definition of the data type
            files_table = data_project.browse_data(data_type, browse_format, \
                                                   tiled_uri = tiled_uri,
                                                   dir_path=self.data_folder_root,
                                                   api_key=self.api_key,
                                                   recursive=False)
            row_indx = next((indx for indx, row in enumerate(files_table) if row.uri in first_uri), None)
            out_table = DataProject(data=files_table).get_table_dict()
        else:
            out_table = files_table
        return out_table, [row_indx], tiled_on