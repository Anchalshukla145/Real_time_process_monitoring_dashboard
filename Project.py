import psutil
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import collections

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Required for deployment

# Store historical data
cpu_history = collections.deque(maxlen=20)
memory_history = collections.deque(maxlen=20)

def update_metrics():
    cpu_history.append(psutil.cpu_percent())
    memory_history.append(psutil.virtual_memory().percent)

# Layout with dark mode toggle
app.layout = html.Div(id='app-container', children=[
    html.Button("🌙 Toggle Dark Mode", id='dark-mode-toggle', n_clicks=0,
                style={'padding': '10px', 'borderRadius': '5px', 'cursor': 'pointer', 'border': 'none'}),
    
    html.H1("System Performance Dashboard", id='title', style={'color': '#333'}),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    
    html.Div(style={'display': 'flex', 'justifyContent': 'space-around'}, children=[
        html.Div([
            html.H3("CPU Usage", style={'color': '#007bff'}),
            dcc.Graph(id='cpu-usage-graph')
        ], style={'width': '45%'}),

        html.Div([
            html.H3("Memory Usage", style={'color': '#dc3545'}),
            dcc.Graph(id='memory-usage-graph')
        ], style={'width': '45%'}),
    ]),
    
    dcc.Store(id='dark-mode-store', storage_type='local')
])

# Callbacks to update graphs & dark mode
@app.callback(
    [Output('cpu-usage-graph', 'figure'), Output('memory-usage-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    update_metrics()
    
    def create_figure(title, data, color):
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=list(data), mode='lines', name=title, line=dict(color=color)))
        fig.update_layout(title=title, xaxis_title='Time', yaxis_title='Usage (%)')
        return fig
    
    return (
        create_figure("CPU Usage", cpu_history, '#007bff'),
        create_figure("Memory Usage", memory_history, '#dc3545')
    )

@app.callback(
    [Output('app-container', 'style'), Output('title', 'style'), Output('dark-mode-store', 'data')],
    [Input('dark-mode-toggle', 'n_clicks')],
    [State('dark-mode-store', 'data')]
)
def toggle_dark_mode(n_clicks, stored_data):
    dark_mode = stored_data if stored_data is not None else False
    dark_mode = not dark_mode  # Toggle state
    
    if dark_mode:
        return ({'backgroundColor': '#1e1e1e', 'color': '#e0e0e0', 'padding': '20px'}, {'color': '#ffffff'}, dark_mode)
    else:
        return ({'backgroundColor': '#f5f5f5', 'color': 'black', 'padding': '20px'}, {'color': '#333'}, dark_mode)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
