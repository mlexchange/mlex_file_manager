import os
import io, shutil, pathlib, base64, math, zipfile

import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq
import dash_uploader as du
from dash.dependencies import Input, Output, State, MATCH, ALL

from flask import Flask
import itertools
import PIL
import plotly.express as px

import templates
from helper_utils import draw_rows
from file_manager import paths_from_dir, filenames_from_dir, move_a_file, move_dir, docker_to_local_path
                         


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets = external_stylesheets, suppress_callback_exceptions=True)

header = templates.header()

NUMBER_OF_ROWS = 4
NUMBER_IMAGES_PER_ROW = 4

DOCKER_DATA = pathlib.Path.home() / 'data'
LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA) 

UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'upload'
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)



# files display
file_paths_table = html.Div(
        children=[
            dash_table.DataTable(
                id='files-table',
                columns=[
                    {'name': 'type', 'id': 'file_type'},
                    {'name': 'File Table', 'id': 'file_path'},
                ],
                data = [],
                hidden_columns = ['file_type'],
                row_selectable='single', #'multi',
                style_cell={'padding': '0.5rem', 'textAlign': 'left'},
                fixed_rows={'headers': False},
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                style_data_conditional=[
                    {'if': {'filter_query': '{file_type} = dir'},
                     'color': 'blue'},
                 ],
                style_table={'height':'18rem', 'overflowY': 'auto'}
            )
        ]
    )


# UPLOAD DATASET OR USE PRE-DEFINED DIRECTORY
data_access = html.Div([
    dbc.Card([
        dbc.CardBody(id='data-body',
                      children=[
                          dbc.Label('1. Upload a new file or a zipped folder:', className='mr-2'),
                          html.Div([du.Upload(
                                            id="dash-uploader",
                                            max_file_size=60000,  # 1800 Mb
                                            cancel_button=True,
                                            pause_button=True
                                    )],
                                    style={  # wrapper div style
                                        'textAlign': 'center',
                                        'width': '770px',
                                        'padding': '5px',
                                        'display': 'inline-block',
                                        'margin-bottom': '10px',
                                        'margin-right': '20px'},
                          ),
                          dbc.Label('2. Choose files/directories:', className='mr-2'),
                          dbc.Row([
                            dbc.Col(
                                dbc.Row([
                                    dbc.Col(dbc.InputGroupText("Browse Format: ", style={'height': '2.5rem', 'width': '100%'}),
                                            width=5),
                                    dbc.Col(dcc.Dropdown(
                                                id='browse-format',
                                                options=[
                                                    {'label': 'dir', 'value': 'dir'},
                                                    {'label': 'all (*)', 'value': '*'},
                                                    {'label': '.png', 'value': '*.png'},
                                                    {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                    {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                    {'label': '.txt', 'value': '*.txt'},
                                                    {'label': '.csv', 'value': '*.csv'},
                                                ],
                                                value='dir',
                                                style={'height': '2.5rem', 'width': '100%'}),
                                            width=7)
                                ], className="g-0"),
                                width=4,
                            ),
                            dbc.Col([
                                dbc.Button("Delete the Selected",
                                             id="delete-files",
                                             className="ms-auto",
                                             color="danger",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '100%', 'height': '2.5rem'}
                                    ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                    dbc.ModalBody("Files cannot be recovered after deletion. Do you still want to proceed?"),
                                    dbc.ModalFooter([
                                        dbc.Button(
                                            "Delete", id="confirm-delete", color='danger', outline=False, 
                                            className="ms-auto", n_clicks=0
                                        )])
                                    ],
                                    id="modal",
                                    is_open=False,
                                    style = {'color': 'red'}
                                )
                            ], width=2),
                            dbc.Col(
                                dbc.Row([
                                    dbc.Col(dbc.InputGroupText("Import Format: ", style={'height': '2.5rem', 'width': '100%'}),
                                            width=5),
                                    dbc.Col(dcc.Dropdown(
                                            id='import-format',
                                            options=[
                                                {'label': 'all files (*)', 'value': '*'},
                                                {'label': '.png', 'value': '*.png'},
                                                {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                {'label': '.txt', 'value': '*.txt'},
                                                {'label': '.csv', 'value': '*.csv'},
                                            ],
                                            value='*',
                                            style={'height': '2.5rem', 'width': '100%'}),
                                            width=7)
                                ], className="g-0"),
                                width=4
                            ),
                            dbc.Col(
                                dbc.Button("Import",
                                             id="import-dir",
                                             className="ms-auto",
                                             color="secondary",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '100%', 'height': '2.5rem'}
                                ),
                                width=2,
                            ),
                          ]),        
                        dbc.Label('3. (Optional) Move a file or folder into a new directory:', className='mr-2'),
                        dbc.Button(
                            "Open File Mover",
                            id="file-mover-button",
                            size="sm",
                            className="mb-3",
                            color="secondary",
                            outline=True,
                            n_clicks=0,
                        ),
                        dbc.Collapse(
                            html.Div([
                                dbc.Col([
                                      dbc.Label("Home data directory (Docker HOME) is '{}'.\
                                                 Dataset is by default uploaded to '{}'. \
                                                 You can move the selected files or directories (from File Table) \
                                                 into a new directory.".format(DOCKER_DATA, UPLOAD_FOLDER_ROOT), className='mr-5'),
                                      html.Div([
                                          dbc.Label('Move data into directory:', className='mr-5'),
                                          dcc.Input(id='dest-dir-name', placeholder="Input relative path to Docker HOME. e.g., test/dataset1", 
                                                        style={'width': '40%', 'margin-bottom': '10px'}),
                                          dbc.Button("Move",
                                               id="move-dir",
                                               className="ms-auto",
                                               color="secondary",
                                               size='sm',
                                               outline=True,
                                               n_clicks=0,
                                               #disabled = True,
                                               style={'width': '22%', 'margin': '5px'}),
                                      ],
                                      style = {'width': '100%', 'display': 'flex', 'align-items': 'center'},
                                      )
                                  ])
                             ]),
                            id="file-mover-collapse",
                            is_open=False,
                        ),
#                         html.Div([ html.Div([dbc.Label('4. (Optional) Load data through Tiled')], style = {'margin-right': '10px'}),
#                                     daq.BooleanSwitch(
#                                         id='tiled-switch',
#                                         on=False,
#                                         color="#9B51E0",
#                                     )],
#                             style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin': '10px', 'margin-left': '0px'},
#                         ),
                        html.Div([ html.Div([dbc.Label('4. (Optional) Show Local/Docker Path')], style = {'margin-right': '10px'}),
                                    daq.ToggleSwitch(
                                        id='my-toggle-switch',
                                        value=False
                                    )],
                            style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin': '10px', 'margin-left': '0px'},
                        ),
                        file_paths_table,
                        ]),
    ],
    id="data-access",
    )
])

file_explorer = html.Div(
    [
        dbc.Button(
            "Toggle File Manager",
            id="collapse-button",
            size="lg",
            className="m-2",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Button(
            "Clear Images",
            id="clear-data",
            size="lg",
            className="m-2",
            color="secondary",
            outline=True,
            n_clicks=0,
            #style={'width': '100%', 'justify-content': 'center'}
        ),
        dbc.Collapse(
            data_access,
            id="collapse",
            is_open=True,
        ),
    ]
)


# DISPLAY DATASET
display = html.Div(
    [
        file_explorer,
        html.Div(id='output-image-upload'),
        dbc.Row([
            dbc.Col(dbc.Row(dbc.Button('<', id='prev-page', style={'width': '10%'}, disabled=True), justify='end')),
            dbc.Col(dbc.Row(dbc.Button('>', id='next-page', style={'width': '10%'}, disabled=True), justify='start'))
        ],justify='center'
        )
    ]
)


browser_cache =html.Div(
        id="no-display",
        children=[            
            dcc.Store(id='docker-file-paths', data=[]),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='dummy-data', data=0)
        ],
    )


#APP LAYOUT
layout = html.Div(
    [
        header,
        dbc.Container(
            [   display
            ],
            fluid=True
        ),
        html.Div(browser_cache)
    ]
)

app.layout = layout

#================================== callback functions ===================================

@app.callback(
    Output("collapse", "is_open"),

    Input("collapse-button", "n_clicks"),
    Input('import-dir', 'n_clicks'),

    State("collapse", "is_open")
)
def toggle_collapse(n, import_n_clicks, is_open):
    if n or import_n_clicks:
        return not is_open
    return is_open


@app.callback(
    Output("file-mover-collapse", "is_open"),
    Input("file-mover-button", "n_clicks"),
    State("file-mover-collapse", "is_open")
)
def file_mover_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("modal", "is_open"),
    Input("delete-files", "n_clicks"),
    Input("confirm-delete", "n_clicks"),  
    State("modal", "is_open")
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output('dummy-data', 'data'),
    [Input('dash-uploader', 'isCompleted')],
    [State('dash-uploader', 'fileNames'),
     State('dash-uploader', 'upload_id')],
)
def upload_zip(iscompleted, upload_filename, upload_id):
    if not iscompleted:
        return 0

    if upload_filename is not None:
        path_to_zip_file = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0]
        if upload_filename[0].split('.')[-1] == 'zip':   # unzip files and delete zip file
            zip_ref = zipfile.ZipFile(path_to_zip_file)  # create zipfile object
            path_to_folder = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0].split('.')[-2]
            if (upload_filename[0].split('.')[-2] + '/') in zip_ref.namelist():
                zip_ref.extractall(pathlib.Path(UPLOAD_FOLDER_ROOT))    # extract file to dir
            else:
                zip_ref.extractall(path_to_folder)

            zip_ref.close()  # close file
            os.remove(path_to_zip_file)

    return 0 


@app.callback(
    Output('files-table', 'data'),
    Output('docker-file-paths', 'data'),

    Input('clear-data', 'n_clicks'),
    Input('browse-format', 'value'),
    Input('import-dir', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    Input('docker-file-paths', 'data'),
    Input('my-toggle-switch', 'value'),
    Input('dummy-data', 'data'),
    Input('files-table', 'selected_rows'),

    State('dest-dir-name', 'value'),
)
def load_dataset(clear_data, browse_format, import_n_clicks, delete_n_clicks, 
                move_dir_n_clicks, selected_paths, docker_path, uploaded_data, rows, dest):
    '''
    This callback displays manages the actions of file manager
    Args:
        clear_data:         Clear loaded images
        browse_format:      File extension to browse
        import_n_clicks:    Import button
        delete_n_clicks:    Delete button
        move_dir_n_clicks:  Move button
        selected_paths:     Selected paths in cache
        docker_path:        [bool] docker vs local path
        dest:               Destination path
        rows:               Selected rows
    Returns
        files:              Filenames to be displayed in File Manager according to browse_format from docker/local path
        selected_files:     List of selected filename FROM DOCKER PATH (no subdirectories)
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    files = paths_from_dir(DOCKER_DATA, browse_format, sort=True)
        
    selected_files = []
    if bool(rows):
        for row in rows:
            selected_files.append(files[row])
    
    if changed_id == 'confirm-delete.n_clicks':
        for filepath in selected_files:
            if os.path.isdir(filepath['file_path']):
               shutil.rmtree(filepath['file_path'])
            else:
                os.remove(filepath['file_path'])
        selected_files = []
        files = paths_from_dir(DOCKER_DATA, browse_format, sort=True)
    
    if changed_id == 'move-dir.n_clicks':
        if dest is None:
            dest = ''
        destination = DOCKER_DATA / dest
        destination.mkdir(parents=True, exist_ok=True)
        if bool(rows):
            sources = selected_paths
            for source in sources:
                if os.path.isdir(source['file_path']):
                    move_dir(source['file_path'], str(destination))
                    shutil.rmtree(source['file_path'])
                else:
                    move_a_file(source['file_path'], str(destination))

            selected_files = []
            files = paths_from_dir(DOCKER_DATA, browse_format)
    
    if changed_id == 'clear-data.n_clicks':
        selected_files = []

    # do not update 'docker-file-paths' when only toggle docker path 
    if selected_files == selected_paths:
        selected_files = dash.no_update

    if docker_path:
        return files, selected_files
    else:
        return docker_to_local_path(files, DOCKER_HOME, LOCAL_HOME), selected_files


@app.callback(
    Output('image-order','data'),
    Input('docker-file-paths','data'),
    Input('import-dir', 'n_clicks'),
    Input('import-format', 'value'),
    Input('files-table', 'selected_rows'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(file_paths, import_n_clicks, import_format, rows,
                  delete_n_clicks, move_dir_n_clicks, image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
    Args:
        file_paths :            Absolute file paths selected from path table
        import_n_clicks:        Button for importing selected paths
        import_format:          File format for import
        rows:                   Rows of the selected file paths from path table
        delete_n_clicks:        Button for deleting selected file paths
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)

    Returns:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        data_access_open:       Closes the reactive component to select the data access (upload vs. directory)
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])

    changed_id = dash.callback_context.triggered[0]['prop_id']
    if import_n_clicks and bool(rows):
        list_filename = []
        if bool(file_paths):
            for file_path in file_paths:
                if file_path['file_type'] == 'dir':
                    list_filename = filenames_from_dir(file_path['file_path'], supported_formats)
                else:
                    list_filename.append(file_path['file_path'])
        else:
            image_order = []
    
        num_imgs = len(list_filename)
        if  changed_id == 'import-dir.n_clicks' or \
            changed_id == 'confirm-delete.n_clicks' or \
            changed_id == 'files-table.selected_rows' or \
            changed_id == 'move_dir_n_clicks':
            image_order = list(range(num_imgs))
            
    else:
        image_order = []

    return image_order


@app.callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('import-format', 'value'),
    Input('docker-file-paths','data'),
    Input('my-toggle-switch', 'value'),

    State('current-page', 'data'),
    State('import-dir', 'n_clicks')],
    prevent_initial_call=True)
def update_output(image_order, button_prev_page, button_next_page, rows, import_format,
                  file_paths, docker_path, current_page, import_n_clicks):
    '''
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        rows:                   Rows of the selected file paths from path table
        import_format:          File format for import
        file_paths:             Absolute file paths selected from path table
        docker_path:            Showing file path in Docker environment
        current_page:           Index of the current page
        import_n_clicks:        Button for importing the selected paths
    Returns:
        children:               Images to be displayed in front-end according to the current page index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])
    
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # update current page if necessary
    if changed_id == 'image-order.data':
        current_page = 0
    if changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    if changed_id == 'next-page.n_clicks':
        current_page = current_page + 1

    children = []
    num_imgs = 0
    if import_n_clicks and bool(rows):
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = filenames_from_dir(file_path['file_path'], supported_formats)
            else:
                list_filename.append(file_path['file_path'])
    
        # plot images according to current page index and number of columns
        num_imgs = len(image_order)
        if num_imgs>0:
            start_indx = NUMBER_OF_ROWS * NUMBER_IMAGES_PER_ROW * current_page
            max_indx = min(start_indx + NUMBER_OF_ROWS * NUMBER_IMAGES_PER_ROW, num_imgs)
            new_contents = []
            new_filenames = []
            for i in range(start_indx, max_indx):
                filename = list_filename[image_order[i]]
                with open(filename, "rb") as file:
                    img = base64.b64encode(file.read())
                    file_ext = filename[filename.find('.')+1:]
                    new_contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                if docker_path:
                    new_filenames.append(list_filename[image_order[i]])
                else:
                    new_filenames.append(docker_to_local_path(list_filename[image_order[i]], DOCKER_HOME, LOCAL_HOME, 'str'))
                
            children = draw_rows(new_contents, new_filenames, NUMBER_IMAGES_PER_ROW, NUMBER_OF_ROWS)

    return children, current_page==0, math.ceil((num_imgs//NUMBER_IMAGES_PER_ROW)/NUMBER_OF_ROWS)<=current_page+1, \
           current_page




if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8060)



