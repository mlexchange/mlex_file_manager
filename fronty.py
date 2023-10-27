import os
import pathlib
import dash
from dash import html, dcc, Output, Input
from dash.long_callback import DiskcacheLongCallbackManager
import dash_uploader as du
import dash_bootstrap_components as dbc
import diskcache
from file_manager.main import FileManager
from file_manager.data_project import DataProject

DOCKER_DATA = pathlib.Path.home() / 'data'
UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'upload'
SPLASH_URL = str(os.environ['SPLASH_URL'])
TILED_KEY = str(os.environ['TILED_KEY'])

#### SETUP DASH APP ####
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
    ]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                long_callback_manager=long_callback_manager)
app.title = "MLExchange Example"

#### SETUP FILE MANAGER ####
dash_file_explorer = FileManager(DOCKER_DATA,
                                 UPLOAD_FOLDER_ROOT,
                                 open_explorer=False,
                                 api_key=TILED_KEY,
                                 splash_uri=SPLASH_URL)
dash_file_explorer.init_callbacks(app)
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)

##### DEFINE LAYOUT ####
app.layout = html.Div(
    [
        dbc.Container(
            [
                html.H1('MLExchange File Manager Example'),
                dash_file_explorer.file_explorer,
                html.P(''),
                dbc.Card([
                    dbc.CardHeader('Data display'),
                    dbc.CardBody(
                        children=[
                            dbc.Row([
                                html.Img(
                                    id='img-output',
                                    style={'width':'20%'}
                                    )
                                ],
                                justify="center",
                            ),
                            dbc.Row([
                                dbc.Label(
                                    id='img-label',
                                    style={'height': '3rem'}
                                    ),
                                ],
                            ),
                            dbc.Row([
                                dcc.Slider(
                                    id='img-slider',
                                    min=0,
                                    step=1,
                                    marks=None,
                                    value=0,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": True
                                        }
                                    )
                            ])
                        ]
                    )
                ])
            ],
            fluid=True,
        )
    ]
)


#### CALLBACKS ####
@app.callback(
    Output('img-output', 'src'),
    Output('img-slider', 'max'),
    Output('img-slider', 'value'),
    Output('img-label', 'children'),
    Input({'base_id': 'file-manager', 'name': 'docker-file-paths'}, 'data'),
    Input('img-slider', 'value'),
    prevent_initial_call=True
)
def refresh_image(file_paths, img_ind):
    '''
    This callback updates the image in the display
    Args:
        file_paths:         Selected data files
        img_ind:            Index of image according to the slider value
    Returns:
        img-output:         Output figure
        img-slider-max:     Maximum value of the slider according to the dataset (train vs test)
        img-slider-value:   Current value of the slider
        label-output:       Output data set uri
    '''
    data_project = DataProject()
    data_project.init_from_dict(file_paths)
    if len(data_project.data) > 0:
        slider_max = len(data_project.data) - 1
        if img_ind > slider_max:
            img_ind = 0
        image, uri = data_project.data[img_ind].read_data()
    else:
        image = dash.no_update
        uri = dash.no_update
        slider_max = 0
        img_ind = 0
    return image, slider_max, img_ind, uri


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')