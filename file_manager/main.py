import os
import pathlib
import pickle
import time
import zipfile

import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from file_manager.dash_file_explorer import create_file_explorer
from file_manager.data_project import DataProject


class FileManager:
    def __init__(
        self,
        data_folder_root,
        upload_folder_root=None,
        max_file_size=60000,
        open_explorer=True,
        api_key=None,
    ):
        """
        FileManager creates a dash file explorer that supports: (1) local file reading, and (2)
        data access through Tiled
        Args:
            data_folder_root:       [str] Root folder to data directory for local loading
            upload_folder_root:     [str] Root folder to upload directory
            max_file_size:          [int] Maximum file size for uploaded data, defaults to 60000
            open_explorer:          [bool] Open/close the file explorer at start up
            api_key:                [str] Tiled API key
        """
        self.data_folder_root = data_folder_root
        self.upload_folder_root = upload_folder_root
        self.max_file_size = max_file_size
        self.api_key = api_key
        self.manager_filename = ".file_manager_vars.pkl"
        # Definition of the dash components for file manager
        self.file_explorer = html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Toggle Explorer",
                                id={
                                    "base_id": "file-manager",
                                    "name": "collapse-button",
                                },
                                n_clicks=0,
                                style={
                                    "width": "100%",
                                    "color": "white",
                                    "background-color": "#007681",
                                    "border-color": "#007681",
                                },
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Refresh Project",
                                id={"base_id": "file-manager", "name": "refresh-data"},
                                color="secondary",
                                n_clicks=0,
                                style={
                                    "width": "100%",
                                    "color": "white",
                                    "background-color": "#007681",
                                    "border-color": "#007681",
                                },
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Clear Images",
                                id={"base_id": "file-manager", "name": "clear-data"},
                                color="danger",
                                n_clicks=0,
                                style={"width": "100%"},
                            ),
                        ),
                        dcc.Loading(
                            id={"base_id": "file-manager", "name": "loading-cube"},
                            type="cube",
                            children=[
                                dbc.Modal(
                                    children=[
                                        dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                        dbc.ModalBody(
                                            children="Could not connect to Tiled"
                                        ),
                                    ],
                                    id={
                                        "base_id": "file-manager",
                                        "name": "tiled-error",
                                    },
                                    is_open=False,
                                    style={"color": "red"},
                                )
                            ],
                            style={"background-color": "transparent"},
                            fullscreen=True,
                        ),
                    ],
                    className="g-0",
                    justify="center",
                ),
                dbc.Row(
                    daq.BooleanSwitch(
                        id={"base_id": "file-manager", "name": "log-toggle"},
                        label="Log",
                        labelPosition="top",
                        style={"display": "none"},
                    ),
                ),
                dbc.Collapse(
                    create_file_explorer(max_file_size, self.upload_folder_root),
                    id={"base_id": "file-manager", "name": "collapse-explorer"},
                    is_open=open_explorer,
                ),
            ]
        )
        pass

    def init_callbacks(self, app):
        """
        Definition of the callbacks to support the functionality of the file manager components
        Args:
            app:        Dash app that contains a file manager
        """
        app.callback(
            Output({"base_id": "file-manager", "name": "collapse-explorer"}, "is_open"),
            [
                Input(
                    {"base_id": "file-manager", "name": "collapse-button"}, "n_clicks"
                ),
                Input({"base_id": "file-manager", "name": "import-dir"}, "n_clicks"),
                Input({"base_id": "file-manager", "name": "refresh-data"}, "n_clicks"),
                State(
                    {"base_id": "file-manager", "name": "collapse-explorer"}, "is_open"
                ),
            ],
        )(self._toggle_collapse)

        app.callback(
            Output({"base_id": "file-manager", "name": "upload-data"}, "data"),
            [
                Input(
                    {"base_id": "file-manager", "name": "dash-uploader"}, "isCompleted"
                ),
                State(
                    {"base_id": "file-manager", "name": "dash-uploader"}, "fileNames"
                ),
            ],
            prevent_initial_call=True,
        )(self._upload_zip)

        app.long_callback(
            Output({"base_id": "file-manager", "name": "files-table"}, "data"),
            [
                Input({"base_id": "file-manager", "name": "browse-format"}, "value"),
                Input({"base_id": "file-manager", "name": "upload-data"}, "data"),
            ],
        )(self._load_file_table)
        pass

        app.long_callback(
            Output({"base_id": "file-manager", "name": "tiled-table"}, "data"),
            Output(
                {"base_id": "file-manager", "name": "tiled-error"},
                "is_open",
                allow_duplicate=True,
            ),
            [
                Input({"base_id": "file-manager", "name": "tiled-browse"}, "n_clicks"),
                State({"base_id": "file-manager", "name": "tiled-uri"}, "value"),
                State({"base_id": "file-manager", "name": "tiled-query"}, "value"),
            ],
            prevent_initial_call=True,
        )(self._load_tiled_table)
        pass

        app.callback(
            Output({"base_id": "file-manager", "name": "files-table"}, "selected_rows"),
            [
                Input({"base_id": "file-manager", "name": "files-table"}, "data"),
                Input(
                    {"base_id": "file-manager", "name": "select-all-files"}, "n_clicks"
                ),
            ],
            prevent_initial_call=True,
        )(self._select_all)
        pass

        app.callback(
            Output({"base_id": "file-manager", "name": "tiled-table"}, "selected_rows"),
            [
                Input({"base_id": "file-manager", "name": "tiled-table"}, "data"),
                Input(
                    {"base_id": "file-manager", "name": "select-all-tiled"}, "n_clicks"
                ),
            ],
            prevent_initial_call=True,
        )(self._select_all)
        pass

        app.long_callback(
            [
                Output(
                    {"base_id": "file-manager", "name": "data-project-dict"}, "data"
                ),
                Output({"base_id": "file-manager", "name": "tiled-error"}, "is_open"),
                Output({"base_id": "file-manager", "name": "tabs"}, "value"),
                Output(
                    {"base_id": "file-manager", "name": "total-num-data-points"}, "data"
                ),
            ],
            [
                Input({"base_id": "file-manager", "name": "import-dir"}, "n_clicks"),
                Input({"base_id": "file-manager", "name": "refresh-data"}, "n_clicks"),
                Input({"base_id": "file-manager", "name": "clear-data"}, "n_clicks"),
                State({"base_id": "file-manager", "name": "tabs"}, "value"),
                State(
                    {"base_id": "file-manager", "name": "confirm-update-data"}, "data"
                ),
                State(
                    {"base_id": "file-manager", "name": "files-table"}, "selected_rows"
                ),
                State(
                    {"base_id": "file-manager", "name": "tiled-table"}, "selected_rows"
                ),
                State({"base_id": "file-manager", "name": "tiled-uri"}, "value"),
                State({"base_id": "file-manager", "name": "files-table"}, "data"),
                State({"base_id": "file-manager", "name": "tiled-table"}, "data"),
                State({"base_id": "file-manager", "name": "import-format"}, "value"),
            ],
        )(self._load_dataset)
        pass

    @staticmethod
    def _toggle_collapse(collapse_n_clicks, import_n_clicks, refresh_n_clicks, is_open):
        """
        Collapse the file manager once a data set has been selected
        Args:
            collapse_n_clicks:  Number of clicks in collapse button
            import_n_clicks:    Number of clicks in import button
            refresh_n_clicks:   Number of clicks on refresh data button
            is_open:            Bool variable indicating if file manager is collapsed or not
        Returns:
            is_open:            Updated state of is_open
        """
        changed_id = dash.callback_context.triggered[0]["prop_id"]
        if "refresh-data" in changed_id or "import" in changed_id:
            return False
        elif collapse_n_clicks:
            return not is_open
        return is_open

    def _upload_zip(self, iscompleted, upload_filename):
        """
        Unzip uploaded files and save them at upload folder root
        Args:
            iscompleted:            Flag indicating if the upload + unzip are complete
            upload_filenames:       List of filenames that were uploaded
        Returns:
            flag:                   Bool indicating if the uploading process is completed
        """
        if not iscompleted:
            return False
        if upload_filename is not None:
            path_to_zip_file = (
                pathlib.Path(self.upload_folder_root) / upload_filename[0]
            )
            if upload_filename[0].split(".")[-1] == "zip":
                zip_ref = zipfile.ZipFile(path_to_zip_file)  # create zipfile object
                path_to_folder = (
                    pathlib.Path(self.upload_folder_root)
                    / upload_filename[0].split(".")[-2]
                )
                if (upload_filename[0].split(".")[-2] + "/") in zip_ref.namelist():
                    zip_ref.extractall(
                        pathlib.Path(self.upload_folder_root)
                    )  # extract file to dir
                else:
                    zip_ref.extractall(path_to_folder)
                zip_ref.close()  # close file
                os.remove(path_to_zip_file)
        return True

    def _load_file_table(self, browse_format, uploaded_data):
        """
        This callback updates the content of the file table
        Args:
            browse_format:      File extension to browse
            uploaded_data:      Flag that indicates if new data has been uploaded
        Returns:
            table_data:         Updated table data according to browsing selection
        """
        data_project = DataProject(
            data_type="file", root_uri=str(self.data_folder_root)
        )
        browse_data = data_project.browse_data(
            browse_format,
        )
        return [{"uri": dataset.uri} for dataset in browse_data]

    def _load_tiled_table(self, browse_n_clicks, tiled_uri, tiled_query):
        """
        This callback updates the content of the tiled table
        Args:
            browse_n_clicks:        Number of clicks on browse Tiled button
            tiled_uri:              Tiled URI for data access
            tiled_query:            Query to be applied to the Tiled URI
        Returns:
            table_data:             Updated table data according to browsing selection
            tiled_warning_modal:    Open warning indicating that the connection to tiled failed
        """
        data_project = DataProject(
            data_type="tiled", root_uri=tiled_uri, api_key=self.api_key
        )
        try:
            browse_data = data_project.browse_data(
                sub_uri_template=tiled_query,
            )
        except Exception as e:
            print(f"Connection to tiled failed: {e}")
            return dash.no_update, True
        return [{"uri": dataset.uri} for dataset in browse_data], False

    def _select_all(self, table_data, select_all_n_clicks):
        """
        This callback selects all rows in the table
        Args:
            table_data:             Current values within the table
            select_all_n_clicks:    Number of clicks on select all button
        Returns:
            selected_rows:          List of selected rows
        """
        if select_all_n_clicks:
            return list(range(len(table_data)))
        return []

    def _load_dataset(
        self,
        import_n_clicks,
        refresh_data,
        clear_data_n_clicks,
        tab_value,
        update_data,
        file_rows,
        tiled_rows,
        tiled_uri,
        files_table,
        tiled_table,
        import_format,
    ):
        """
        This callback manages the actions of file manager
        Args:
            browse_format:          File extension to browse
            import_n_clicks:        Number of clicks on import button
            refresh_data:           Number of clicks on refresh data button
            uploaded_data:          Flag that indicates if new data has been uploaded
            clear_data_n_clicks:    Number of clicks on clear data button
            tab_value:              Tab indicating data access method (filesystem/tiled)
            update_data:            Flag that indicates if the dataset can be updated
            file_rows:              Selected rows in table of files/directories
            tiled_rows:             Selected rows in table of tiled data
            tiled_uri:              Tiled URI for data access
            files_table:            Current values within the table of files/directories/nodes
            tiled_table:            Current values within the table of tiled data
            import_format:          File extension to import
        Returns:
            data_project_dict:      Dictionary containing the data project
            tiled_warning_modal:    Open warning indicating that the connection to tiled failed
            tab_value:              Tab indicating data access method (filesystem/tiled)
            total_num_data_points:  Total number of data points in the data project
        """
        start = time.time()
        changed_id = dash.callback_context.triggered[0]["prop_id"]
        data_project = DataProject(
            data_type=tab_value,
            root_uri=str(self.data_folder_root) if tab_value == "file" else tiled_uri,
            api_key=self.api_key,
        )
        # prevent update according to update_data flag
        if (
            changed_id
            in [
                '{"base_id":"file-manager","name":"clear-data"}.n_clicks',
                '{"base_id":"file-manager","name":"refresh-data"}.n_clicks',
                '{"base_id":"file-manager","name":"import-dir"}.n_clicks',
            ]
            and not update_data
        ):
            raise PreventUpdate

        elif "clear-data" in changed_id:
            return {}, dash.no_update, dash.no_update, dash.no_update

        elif "refresh-data" in changed_id and os.path.exists(self.manager_filename):
            print("Refreshing data", flush=True)
            with open(self.manager_filename, "rb") as file:
                data_project_dict = pickle.load(file)
            data_project = DataProject.from_dict(data_project_dict)
            print(f"Done after {time.time() - start}")
            return (
                data_project_dict,
                dash.no_update,
                tab_value,
                data_project.datasets[-1].cumulative_data_count,
            )

        if tab_value != "tiled" and bool(file_rows):
            selected_rows = []
            for row in file_rows:
                selected_rows.append(files_table[row]["uri"])
            data_project.datasets = data_project.browse_data(
                import_format,
                selected_sub_uris=selected_rows,
            )

        elif bool(tiled_rows):
            selected_rows = []
            for row in tiled_rows:
                selected_rows.append(tiled_table[row]["uri"])
            try:
                data_project.datasets = data_project.browse_data(
                    "",
                    selected_sub_uris=selected_rows,
                )
            except Exception as e:
                print(f"Connection to tiled failed: {e}")
                return [], True, tab_value, dash.no_update

        if len(data_project.datasets) == 0:
            total_num_data_points = 0
        else:
            total_num_data_points = data_project.datasets[-1].cumulative_data_count

        data_project_dict = data_project.to_dict()

        if len(data_project.datasets) > 0:
            with open(self.manager_filename, "wb") as file:
                pickle.dump(
                    data_project_dict,
                    file,
                )

        print(f"Done after {time.time() - start}", flush=True)
        return data_project_dict, dash.no_update, dash.no_update, total_num_data_points
