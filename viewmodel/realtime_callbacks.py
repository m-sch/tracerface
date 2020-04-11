'''
This module contains all callbacks regarding the realtime tracing
'''
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import view.alerts as alerts


# Disable function managagement buttons if no function is selected
def disable_manage_app_buttons(app):
    output = [
        Output('manage-functions-button', 'disabled'),
        Output('remove-app-button', 'disabled')
    ]
    input = [Input('applications-select', 'value')]
    @app.callback(output, input)
    def disable(app):
        disabled = not app
        return disabled, disabled


# Disable function managagement buttons if no function is selected
# or if application is already added
def disable_add_app_button(app, view_model):
    output = Output('add-app-button', 'disabled')
    input = [
        Input('application-path', 'value'),
        Input('applications-select', 'options')
    ]
    @app.callback(output, input)
    def disable(app, options):
        return not app or app in view_model.get_apps()


# Disable config load button if no path is provided
def disable_load_config_button(app):
    output = Output('load-config-button', 'disabled')
    input = [Input('config-file-path', 'value')]
    @app.callback(output, input)
    def disable(path):
        return not path


# Stop tracing if an error occurs
def stop_trace_on_error(app, view_model):
    output = [
        Output('trace-button', 'on'),
        Output('trace-error-notification', 'children')
    ]
    input = [Input('timer', 'n_intervals')]
    state = [State('trace-button', 'on')]
    @app.callback(output, input, state)
    def stop_trace(timer_tick, trace_on):
        if timer_tick and trace_on:
            if view_model.thread_error():
                return False, alerts.trace_error_alert(view_model.thread_error())
            elif view_model.process_error():
                return False, alerts.trace_error_alert(view_model.process_error())
            elif not view_model.trace_active():
                return False, alerts.trace_error_alert('Tracing stopped unexpected')
        raise PreventUpdate


# TODO: if no functions, don't let turn on
# Start realtime tracing
def start_or_stop_trace(app, view_model):
    output = Output('timer', 'disabled')
    input = [Input('trace-button', 'on')]
    state = [State('timer', 'disabled')]
    @app.callback(output, input, state)
    def switch_state(trace_on, timer_disabled):
        if trace_on:
            view_model.start_trace()
        elif not timer_disabled:
            view_model.stop_trace()
        return not trace_on


# Disable parts of the interface while tracing is active
def disable_interface_on_trace(app):
    output = [
        Output('static-tab', 'disabled'),
        Output('utilities-tab', 'disabled')
    ]
    input = [Input('timer', 'disabled')]
    @app.callback(output, input)
    def switch_disables(timer_off):
        trace_on = not timer_off
        return trace_on, trace_on


# Add or remove applications, load content of config file
def update_apps_dropdown_options(app, view_model):
    output = [
        Output('applications-select', 'options'),
        Output('add-app-notification', 'children')
    ]
    input = [
        Input('add-app-button', 'n_clicks'),
        Input('remove-app-button', 'n_clicks'),
        Input('load-config-button', 'n_clicks')
    ]
    state = [
        State('application-path', 'value'),
        State('applications-select', 'value'),
        State('config-file-path', 'value')
    ]
    @app.callback(output, input, state)
    def update_options(add, remove, load, app_to_add, app_to_remove, config_path):
        if not callback_context.triggered:
            raise PreventUpdate
        id = callback_context.triggered[0]['prop_id'].split('.')[0]

        alert = None
        if id == 'add-app-button':
            try:
                view_model.add_app(app_to_add)
                alert = alerts.add_app_success_alert(app_to_add)
            except ValueError as msg:
                alert = alerts.ErrorAlert(str(msg))
        elif id == 'remove-app-button':
            view_model.remove_app(app_to_remove)
        elif id == 'load-config-button':
            try:
                view_model.load_config_file(config_path)
                alert = alerts.load_setup_success_alert(config_path)
            except ValueError as msg:
                alert = alerts.ErrorAlert(str(msg))
        return [{"label": app, "value": app} for app in view_model.get_apps()], alert


# Update value of application selection on application removal
def clear_selected_app(app):
    @app.callback(Output('applications-select', 'value'),
        [Input('remove-app-button', 'n_clicks')])
    def clear_value(remove):
        if remove:
            return None
        raise PreventUpdate
