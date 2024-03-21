import dash_bootstrap_components as dbc
from dash import dcc, html


def parse_contents(index):
    """
    This function creates the dash components to display thumbnail images
    Args:
        index:          Index of the dash component
    Returns:
        dash component
    """
    img_card = html.Div(
        children=[
            dbc.Card(
                id={"type": "thumbnail-card", "index": index},
                children=[
                    html.A(
                        id={"type": "thumbnail-image", "index": index},
                        children=[
                            dbc.CardImg(
                                id={"type": "thumbnail-src", "index": index},
                                style={
                                    "width": "100%",
                                    "margin": "auto",
                                    "display": "block",
                                },
                                bottom=False,
                            ),
                        ],
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                id={"type": "thumbnail-name", "index": index},
                            ),
                        ],
                    ),
                    dcc.Store(
                        id={"type": "processed-data-store", "index": index}, data=None
                    ),
                ],
                outline=False,
                style={"display": "none"},
            )
        ],
    )
    return img_card


def draw_rows(n_rows, n_cols):
    """
    This function display the images per page
    Args:
        n_rows:             Number of rows
        n_cols:             Number of columns
    Returns:
        dash component with all the images
    """
    n_cols = n_cols
    children = []
    for j in range(n_rows):
        row_child = []
        for i in range(n_cols):
            row_child.append(
                dbc.Col(
                    parse_contents(j * n_cols + i),
                    width="{}".format(12 // n_cols),
                )
            )
        children.append(dbc.Row(row_child, className="g-1"))
    return children
