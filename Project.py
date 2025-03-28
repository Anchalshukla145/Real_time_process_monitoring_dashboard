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
cpu_history = collections.deque(maxlen=30)
memory_history = collections.deque(maxlen=30)
process_list = []

def update_metrics():
    """Fetch system metrics and update process list"""
    cpu_history.append(psutil.cpu_percent())
    memory_history.append(psutil.virtual_memory().percent)
    
    global process_list
    process_list = [
        (p.info['pid'], p.info['name'], p.info['cpu_percent'], p.info['memory_info'].rss / (1024 * 1024))
        for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info'])
    ]
    process_list.sort(key=lambda x: x[2], reverse=True)  # Sort by CPU usage

# Layout with improved styling
app.layout = html.Div(id='app-container', children=[
    html.Button("🌙 Toggle Dark Mode", id='dark-mode-toggle', n_clicks=0,
                style={'padding': '10px', 'borderRadius': '5px', 'cursor': 'pointer', 'border': 'none'}),

    html.H1("System Performance Dashboard", id='title', style={'color': '#333', 'textAlign': 'center'}),
    
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'gap': '20px'}, children=[
        html.Div([
            html.H3("CPU Usage", style={'color': '#007bff', 'textAlign': 'center'}),
            dcc.Graph(id='cpu-usage-graph', style={'height': '350px'})
        ], style={'width': '48%', 'border': '1px solid #ddd', 'borderRadius': '10px', 'padding': '10px', 'backgroundColor': '#fff'}),

        html.Div([
            html.H3("Memory Usage", style={'color': '#dc3545', 'textAlign': 'center'}),
            dcc.Graph(id='memory-usage-graph', style={'height': '350px'})
        ], style={'width': '48%', 'border': '1px solid #ddd', 'borderRadius': '10px', 'padding': '10px', 'backgroundColor': '#fff'})
    ]),
    
    html.H3("Running Processes", style={'color': '#28a745', 'textAlign': 'center'}),

    html.Div([
        html.Table(id='process-table', style={
            'width': '100%', 
            'borderCollapse': 'collapse',
            'backgroundColor': '#f9f9f9',  
            'borderRadius': '10px',
            'padding': '10px',
            'boxShadow': '2px 2px 10px rgba(0,0,0,0.1)'
        }),
        html.Button("Show More", id='show-more-btn', n_clicks=0, style={'marginTop': '10px', 'padding': '10px', 'display': 'block', 'margin': 'auto'})
    ], style={'overflowX': 'auto'}),

    dcc.Store(id='dark-mode-store', storage_type='local'),
    dcc.Store(id='show-more-store', storage_type='memory', data=False)
])

# Callback to update graphs & process table
@app.callback(
    [Output('cpu-usage-graph', 'figure'), 
     Output('memory-usage-graph', 'figure'), 
     Output('process-table', 'children'), 
     Output('show-more-store', 'data')],
    [Input('interval-component', 'n_intervals'), 
     Input('show-more-btn', 'n_clicks')],
    [State('show-more-store', 'data')]
)
def update_dashboard(n, show_more_clicks, show_all):
    update_metrics()
    
    # Toggle Show More button
    if show_more_clicks:
        show_all = not show_all
    
    displayed_processes = process_list[:20] if not show_all else process_list
    
    def create_figure(title, data, color):
        """Generate a line graph for CPU and memory usage"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=list(data), mode='lines', name=title, line=dict(color=color)))
        fig.update_layout(title=title, xaxis_title='Time', yaxis_title='Usage (%)',
                          template='plotly_white',
                          height=350)
        return fig
    
    # Generate process table
    table_header = html.Tr([
        html.Th("PID", style={'padding': '8px', 'textAlign': 'center', 'backgroundColor': '#dff0d8', 'border': '1px solid #ddd'}),
        html.Th("Name", style={'padding': '8px', 'textAlign': 'center', 'backgroundColor': '#dff0d8', 'border': '1px solid #ddd'}),
        html.Th("CPU (%)", style={'padding': '8px', 'textAlign': 'center', 'backgroundColor': '#dff0d8', 'border': '1px solid #ddd'}),
        html.Th("Memory (MB)", style={'padding': '8px', 'textAlign': 'center', 'backgroundColor': '#dff0d8', 'border': '1px solid #ddd'})
    ])

    table_rows = [
        html.Tr([
            html.Td(pid, style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #ddd'}),
            html.Td(name, style={'padding': '8px', 'textAlign': 'left', 'border': '1px solid #ddd'}),
            html.Td(f"{cpu:.1f}", style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #ddd'}),
            html.Td(f"{mem:.1f}", style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #ddd'})
        ], style={'backgroundColor': '#f2f2f2' if i % 2 == 0 else '#ffffff'})  # Alternating row colors
        for i, (pid, name, cpu, mem) in enumerate(displayed_processes)
    ]

    return (
        create_figure("CPU Usage", cpu_history, '#007bff'),
        create_figure("Memory Usage", memory_history, '#dc3545'),
        [table_header] + table_rows,
        show_all
    )

# Dark mode toggle with persistent state
@app.callback(
    [Output('app-container', 'style'), 
     Output('title', 'style'), 
     Output('dark-mode-store', 'data')],
    [Input('dark-mode-toggle', 'n_clicks')],
    [State('dark-mode-store', 'data')]
)
def toggle_dark_mode(n_clicks, stored_data):
    dark_mode = not stored_data if stored_data is not None else True

    dark_style = {'backgroundColor': '#1e1e1e', 'color': '#e0e0e0', 'padding': '20px'}
    light_style = {'backgroundColor': '#f5f5f5', 'color': 'black', 'padding': '20px'}

    return (dark_style if dark_mode else light_style, 
            {'color': '#ffffff'} if dark_mode else {'color': '#333'}, 
            dark_mode)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
