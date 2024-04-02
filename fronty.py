import os
import time

import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import dash_uploader as du
import diskcache
from dash import ALL, MATCH, ClientsideFunction, Input, Output, State, dcc, html
from dash.long_callback import DiskcacheLongCallbackManager
from flask_caching import Cache

from file_manager.data_project import DataProject
from file_manager.main import FileManager
from plot_utils import draw_rows

READ_DIR = "data"
UPLOAD_FOLDER_ROOT = "data/upload"
SPLASH_URL = os.environ.get("SPLASH_URL", "http://splash:80/api/v0")
TILED_KEY = os.environ.get("TILED_KEY", "")
NUM_ROWS = 3
NUM_COLS = 6
TIMEOUT = 60

# SETUP DASH APP
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)
memoize_cache = Cache(config={"CACHE_TYPE": "filesystem", "CACHE_DIR": "./cache"})

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    long_callback_manager=long_callback_manager,
)
app.title = "MLExchange Example"
memoize_cache.init_app(app.server)

# SETUP FILE MANAGER
dash_file_explorer = FileManager(
    READ_DIR,
    UPLOAD_FOLDER_ROOT,
    open_explorer=True,
    api_key=TILED_KEY,
    splash_uri=SPLASH_URL,
)
dash_file_explorer.init_callbacks(app)
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)

# DEFINE LAYOUT
app.layout = html.Div(
    [
        dbc.Container(
            [
                html.H1("MLExchange File Manager Example"),
                dash_file_explorer.file_explorer,
                html.P(""),
                dbc.Card(
                    [
                        dbc.CardHeader("Data display"),
                        dbc.CardBody(
                            children=dcc.Tabs(
                                id="viz-mode",
                                value="gallery",
                                children=[
                                    dcc.Tab(
                                        label="Gallery",
                                        value="gallery",
                                        children=draw_rows(NUM_ROWS, NUM_COLS)
                                        + [
                                            dbc.Row(
                                                [
                                                    dbc.Button(
                                                        className="fa fa-chevron-left",
                                                        id="prev-page",
                                                        style={"width": "5%"},
                                                    ),
                                                    dbc.Button(
                                                        className="fa fa-chevron-right",
                                                        id="next-page",
                                                        style={"width": "5%"},
                                                    ),
                                                ]
                                            ),
                                            dcc.Store(id="current-page", data=0),
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="Single Image",
                                        value="single",
                                        children=[
                                            dbc.Row(
                                                [
                                                    html.Img(
                                                        id="img-output",
                                                        style={"width": "20%"},
                                                    )
                                                ],
                                                #  html.Canvas(id='image-canvas'),],
                                                justify="center",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Label(
                                                        id="img-label",
                                                        style={"height": "3rem"},
                                                    ),
                                                ],
                                            ),
                                            dbc.Row(
                                                [
                                                    dcc.Slider(
                                                        id="img-slider",
                                                        min=0,
                                                        step=1,
                                                        marks=None,
                                                        value=0,
                                                        tooltip={
                                                            "placement": "bottom",
                                                            "always_visible": True,
                                                        },
                                                    )
                                                ]
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        daq.BooleanSwitch(
                            id="log-transform", on=False, label="Log transform"
                        ),
                        dbc.Button("Download", id="download-button"),
                        dcc.Store(id="download-data"),
                        dcc.Store(id="unit-processed-data-store", data=None),
                    ]
                ),
            ],
            fluid=True,
        )
    ]
)


# CALLBACKS
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="transform_image"),
    Output({"type": "thumbnail-src", "index": MATCH}, "src"),
    Input("log-transform", "on"),
    Input({"type": "thumbnail-src", "index": MATCH}, "src"),
    State({"type": "processed-data-store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)


app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="transform_image"),
    Output("img-output", "src"),
    Input("log-transform", "on"),
    Input("img-output", "src"),
    State("unit-processed-data-store", "data"),
    prevent_initial_call=True,
)


@app.callback(
    Output({"type": "thumbnail-src", "index": MATCH}, "src", allow_duplicate=True),
    Input({"type": "processed-data-store", "index": MATCH}, "data"),
    State({"type": "thumbnail-card", "index": MATCH}, "id"),
    prevent_initial_call=True,
)
def update_thumbnail(processed_data, id):
    # Update your thumbnails using the processed data from the dcc.Store
    # Here, you can extract the specific part of the data relevant to this thumbnail
    # based on its index or any other identifier included in the 'id' state
    if processed_data is None:
        return ""

    # Example assuming processed_data is a list of dicts where each dict contains
    # 'style', 'name', and 'src' keys for each thumbnail
    return processed_data


@app.callback(
    Output({"type": "thumbnail-card", "index": ALL}, "style"),
    Output({"type": "thumbnail-name", "index": ALL}, "children"),
    Output({"type": "processed-data-store", "index": ALL}, "data"),
    Input({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    Input("current-page", "data"),
    prevent_initial_call=True,
)
@memoize_cache.memoize(timeout=TIMEOUT)
def update_page(data_project_dict, current_page):
    """
    This callback updates the page
    """
    log = False
    if data_project_dict:
        data_project = DataProject.from_dict(data_project_dict)
        if len(data_project.datasets) > 0:
            n_images = NUM_ROWS * NUM_COLS
            start = current_page * n_images
            end = (current_page + 1) * n_images
            if end > data_project.datasets[-1].cumulative_data_count:
                end = data_project.datasets[-1].cumulative_data_count
            start_time = time.time()
            src_data, filenames = data_project.read_datasets(
                list(range(start, end)),
                log=log,
            )
            print(
                f"Time to read page {current_page} {len(src_data)} images: {time.time() - start_time}",
                flush=True,
            )
            return [{"display": "block"}] * len(filenames), filenames, src_data
    return (
        [{"display": "None"}] * NUM_ROWS * NUM_COLS,
        [""] * NUM_ROWS * NUM_COLS,
        [""] * NUM_ROWS * NUM_COLS,
    )


@app.callback(
    Output("current-page", "data", allow_duplicate=True),
    Input("prev-page", "n_clicks"),
    State("current-page", "data"),
    prevent_initial_call=True,
)
def update_page_prev(prev_page, current_page):
    if current_page > 0:
        return current_page - 1
    return current_page


@app.callback(
    Output("current-page", "data", allow_duplicate=True),
    Input("next-page", "n_clicks"),
    State("current-page", "data"),
    State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    prevent_initial_call=True,
)
def update_page_next(next_page, current_page, total_num_data_points):
    n_images = NUM_ROWS * NUM_COLS
    n_pages = total_num_data_points // n_images + 1
    if current_page < n_pages - 1:
        return current_page + 1
    return current_page


@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
)
def download_data(n_clicks, data_project_dict):
    if n_clicks:
        data_project = DataProject.from_dict(data_project_dict)
        data_project.tiled_to_local_project([0, 2, 4])
        return "download"
    return dash.no_update


@app.callback(
    Output("unit-processed-data-store", "data"),
    Output("img-slider", "max"),
    Output("img-slider", "value"),
    Output("img-label", "children"),
    Input({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    Input("img-slider", "value"),
    prevent_initial_call=True,
)
def refresh_image(data_project_dict, img_ind):
    """
    This callback updates the image in the display
    Args:
        file_paths:         Selected data files
        img_ind:            Index of image according to the slider value
    Returns:
        img-output:         Output figure
        img-slider-max:     Maximum value of the slider according to the dataset (train vs test)
        img-slider-value:   Current value of the slider
        label-output:       Output data set uri
    """
    if data_project_dict:
        data_project = DataProject.from_dict(data_project_dict)
        if len(data_project.datasets) > 0:
            slider_max = data_project.datasets[-1].cumulative_data_count - 1
            if img_ind > slider_max:
                img_ind = 0
            image, uri = data_project.read_datasets([img_ind], log=False)
            image = image[0]
            uri = uri[0]
        else:
            image = dash.no_update
            uri = dash.no_update
            slider_max = 0
            img_ind = 0
        return image, slider_max, img_ind, uri
    else:
        return None, 0, 0, ""


@app.callback(
    Output("img-output", "src", allow_duplicate=True),
    Input("unit-processed-data-store", "data"),
    prevent_initial_call=True,
)
def update_image(image):
    if image is None:
        print("No image", flush=True)
        return ""
    print("There is an image", flush=True)
    return image


if __name__ == "__main__":
    app.run_server(debug=True)
