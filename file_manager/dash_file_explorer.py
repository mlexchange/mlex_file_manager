import os

import dash_bootstrap_components as dbc
import dash_uploader as du
from dash import dash_table, dcc, html

DEFAULT_TILED_URI = os.getenv("DEFAULT_TILED_URI", "")
DEFAULT_TILED_QUERY = os.getenv("DEFAULT_TILED_QUERY", "")


def create_file_explorer(max_file_size, default_tiled_uri=""):
    """
    Creates the dash components for the file explorer
    Args:
        max_file_size:      Maximum file size to be uploaded
        default_tiled_uri:  Default Tiled URI to be displayed in file manager
    Returns:
        file_explorer:      HTML.DIV with all the corresponding components of the file explorer
    """
    file_explorer = html.Div(
        [
            dbc.Card(
                [
                    dbc.CardBody(
                        id={"base_id": "file-manager", "name": "data-body"},
                        children=[
                            dcc.Tabs(
                                id={"base_id": "file-manager", "name": "tabs"},
                                value="file",
                                children=[
                                    dcc.Tab(
                                        label="Filesystem",
                                        value="file",
                                        children=[
                                            # UPLOADING DATA
                                            html.P(),
                                            dbc.Label(
                                                "Upload a new file or a zipped folder:",
                                                style={
                                                    "margin-right": "10px",
                                                    "margin-bottom": "10px",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    du.Upload(
                                                        id={
                                                            "base_id": "file-manager",
                                                            "name": "dash-uploader",
                                                        },
                                                        max_file_size=max_file_size,
                                                        cancel_button=True,
                                                        pause_button=True,
                                                        default_style={
                                                            "minHeight": 1,
                                                            "lineHeight": 1,
                                                        },
                                                    )
                                                ],
                                                style={
                                                    "textAlign": "center",
                                                    "width": "100%",
                                                    "padding": "5px",
                                                    "display": "inline-block",
                                                    "margin-bottom": "10px",
                                                    "margin-right": "20px",
                                                },
                                            ),
                                            # FILE TABLE
                                            dbc.Button(
                                                "Select all",
                                                id={
                                                    "base_id": "file-manager",
                                                    "name": "select-all-files",
                                                },
                                                n_clicks=0,
                                                color="primary",
                                                outline=True,
                                                style={"margin-top": "10px"},
                                            ),
                                            dbc.Row(
                                                children=[
                                                    dash_table.DataTable(
                                                        id={
                                                            "base_id": "file-manager",
                                                            "name": "files-table",
                                                        },
                                                        columns=[
                                                            {
                                                                "name": "URI",
                                                                "id": "uri",
                                                            },
                                                        ],
                                                        data=[],
                                                        page_size=5,
                                                        hidden_columns=["type"],
                                                        row_selectable="multi",
                                                        style_cell={
                                                            "padding": "0.5rem",
                                                            "textAlign": "left",
                                                        },
                                                        fixed_rows={"headers": False},
                                                        css=[
                                                            {
                                                                "selector": ".show-hide",
                                                                "rule": "display: none",
                                                            }
                                                        ],
                                                        style_data_conditional=[
                                                            {
                                                                "if": {
                                                                    "filter_query": "{file_type} = dir"
                                                                },
                                                                "color": "blue",
                                                            },
                                                        ],
                                                        style_table={
                                                            "overflowY": "auto",
                                                        },
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="Tiled",
                                        value="tiled",
                                        children=[
                                            # TILED FOR DATA ACCESS
                                            html.P(),
                                            dbc.Label(
                                                "Load data through Tiled:",
                                                style={
                                                    "margin-right": "10px",
                                                    "margin-bottom": "10px",
                                                },
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.InputGroup(
                                                            [
                                                                dbc.InputGroupText(
                                                                    "URI"
                                                                ),
                                                                dbc.Textarea(
                                                                    placeholder=DEFAULT_TILED_URI,
                                                                    value="",
                                                                    style={
                                                                        "height": "12px",
                                                                    },
                                                                    id={
                                                                        "base_id": "file-manager",
                                                                        "name": "tiled-uri",
                                                                    },
                                                                ),
                                                            ]
                                                        ),
                                                        width=5,
                                                    ),
                                                    dbc.Col(
                                                        dbc.InputGroup(
                                                            [
                                                                dbc.InputGroupText(
                                                                    "Query"
                                                                ),
                                                                dbc.Textarea(
                                                                    placeholder=DEFAULT_TILED_QUERY,
                                                                    value="",
                                                                    style={
                                                                        "height": "12px",
                                                                    },
                                                                    id={
                                                                        "base_id": "file-manager",
                                                                        "name": "tiled-query",
                                                                    },
                                                                ),
                                                            ]
                                                        ),
                                                        width=5,
                                                    ),
                                                    dbc.Col(
                                                        dbc.Button(
                                                            "Browse Tiled",
                                                            id={
                                                                "base_id": "file-manager",
                                                                "name": "tiled-browse",
                                                            },
                                                            color="primary",
                                                            outline=True,
                                                            n_clicks=0,
                                                            style={"width": "100%"},
                                                        ),
                                                        width=2,
                                                    ),
                                                ]
                                            ),
                                            # TILED TABLE
                                            dbc.Button(
                                                "Select all",
                                                id={
                                                    "base_id": "file-manager",
                                                    "name": "select-all-tiled",
                                                },
                                                n_clicks=0,
                                                color="primary",
                                                outline=True,
                                                style={"margin-top": "10px"},
                                            ),
                                            dbc.Row(
                                                children=[
                                                    dash_table.DataTable(
                                                        id={
                                                            "base_id": "file-manager",
                                                            "name": "tiled-table",
                                                        },
                                                        columns=[
                                                            {
                                                                "name": "URI",
                                                                "id": "uri",
                                                            },
                                                        ],
                                                        data=[],
                                                        page_size=5,
                                                        hidden_columns=["type"],
                                                        row_selectable="multi",
                                                        style_cell={
                                                            "padding": "0.5rem",
                                                            "textAlign": "left",
                                                        },
                                                        fixed_rows={"headers": False},
                                                        css=[
                                                            {
                                                                "selector": ".show-hide",
                                                                "rule": "display: none",
                                                            }
                                                        ],
                                                        style_table={
                                                            "overflowY": "auto",
                                                        },
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            # BROWSE/IMPORT DATA FORMATS
                            dbc.Label(
                                "Choose file formats:",
                                className="mr-2",
                                style={"display": "None"},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.InputGroupText(
                                                        "Browse: ",
                                                        style={
                                                            "height": "2.5rem",
                                                            "margin-bottom": "10px",
                                                            "width": "100%",
                                                        },
                                                    ),
                                                    width=5,
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id={
                                                            "base_id": "file-manager",
                                                            "name": "browse-format",
                                                        },
                                                        options=[
                                                            {
                                                                "label": "dir",
                                                                "value": "**/",
                                                            },
                                                            {
                                                                "label": "all (*)",
                                                                "value": "*",
                                                            },
                                                            {
                                                                "label": ".png",
                                                                "value": "**/*.png",
                                                            },
                                                            {
                                                                "label": ".jpg/jpeg",
                                                                "value": "**/*.jpg",
                                                            },
                                                            {
                                                                "label": ".tif/tiff",
                                                                "value": "**/*.tif",
                                                            },
                                                            {
                                                                "label": ".txt",
                                                                "value": "**/*.txt",
                                                            },
                                                            {
                                                                "label": ".csv",
                                                                "value": "**/*.csv",
                                                            },
                                                        ],
                                                        value="**/",
                                                        style={
                                                            "height": "2.5rem",
                                                            "width": "100%",
                                                        },
                                                    ),
                                                    width=7,
                                                ),
                                            ],
                                            className="g-0",
                                        ),
                                        width=5,
                                    ),
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.InputGroupText(
                                                        "Import: ",
                                                        style={
                                                            "height": "2.5rem",
                                                            "width": "100%",
                                                        },
                                                    ),
                                                    width=5,
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id={
                                                            "base_id": "file-manager",
                                                            "name": "import-format",
                                                        },
                                                        options=[
                                                            {
                                                                "label": "all (*)",
                                                                "value": "*",
                                                            },
                                                            {
                                                                "label": ".png",
                                                                "value": "**/*.png",
                                                            },
                                                            {
                                                                "label": ".jpg/jpeg",
                                                                "value": "**/*.jpg",
                                                            },
                                                            {
                                                                "label": ".tif/tiff",
                                                                "value": "**/*.tif",
                                                            },
                                                            {
                                                                "label": ".txt",
                                                                "value": "**/*.txt",
                                                            },
                                                            {
                                                                "label": ".csv",
                                                                "value": "**/*.csv",
                                                            },
                                                        ],
                                                        value="*",
                                                        style={
                                                            "height": "2.5rem",
                                                            "width": "100%",
                                                        },
                                                    ),
                                                    width=7,
                                                ),
                                            ],
                                            className="g-0",
                                        ),
                                        width=5,
                                    ),
                                ],
                                className="g-2",
                                style={"display": "None"},
                            ),
                            # IMPORT BUTTON
                            dbc.Row(
                                dbc.Button(
                                    "Import",
                                    id={
                                        "base_id": "file-manager",
                                        "name": "import-dir",
                                    },
                                    color="primary",
                                    n_clicks=0,
                                    style={"width": "40%", "margin-top": "10px"},
                                ),
                                justify="center",
                            ),
                        ],
                    ),
                    # CACHE
                    dcc.Store(
                        id={"base_id": "file-manager", "name": "data-project-dict"},
                        data=[],
                    ),
                    dcc.Store(
                        id={"base_id": "file-manager", "name": "confirm-update-data"},
                        data=True,
                    ),
                    dcc.Store(
                        id={"base_id": "file-manager", "name": "confirm-clear-data"},
                        data=False,
                    ),
                    dcc.Store(
                        id={"base_id": "file-manager", "name": "upload-data"},
                        data=False,
                    ),
                    dcc.Store(
                        id={"base_id": "file-manager", "name": "total-num-data-points"},
                        data=0,
                    ),
                ]
            ),
        ]
    )
    return file_explorer
