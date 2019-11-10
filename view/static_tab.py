import dash_html_components as html
import dash_bootstrap_components as dbc

from view.styles import button_style, tab_style


# ironically static tab is actually static
class StaticTab:
    def tab(self):
        return html.Div([
            dbc.FormGroup([
                dbc.Label('Trace output'),
                dbc.Textarea(
                    id='output-textarea',
                    placeholder='Enter trace output',
                    style={'height': '200px'}),
                dbc.Button('Submit',
                    id='submit-button',
                    color='primary',
                    className='mr-1',
                    style=button_style()),
                html.Div(
                    id='load-output-notification',
                    children=None,
                    style=button_style())
            ])
        ],
        style=tab_style())