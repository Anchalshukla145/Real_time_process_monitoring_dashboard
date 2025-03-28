import psutil
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import collections

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# Store historical data
cpu_history = collections.deque(maxlen=20)
memory_history = collections.deque(maxlen=20)
disk_usage = collections.deque(maxlen=20)
network_usage = collections.deque(maxlen=20)
process_list = []

def update_metrics():
    """Fetch system metrics and update process list"""
    cpu_history.append(psutil.cpu_percent())
    memory_history.append(psutil.virtual_memory().percent)
    disk_usage.append(psutil.disk_usage('/').percent)
    network_usage.append(psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)
    
    global process_list
    process_list = [
        (p.info['pid'], p.info['name'], p.info['cpu_percent'], p.info['memory_info'].rss / (1024 * 1024))
        for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info'])
    ]
    process_list.sort(key=lambda x: x[2], reverse=True)

def kill_process(pid):
    """Terminate a process by PID"""
    try:
        p = psutil.Process(pid)
        p.terminate()
        return f"Process {pid} terminated successfully"
    except Exception as e:
        return f"Error terminating process {pid}: {str(e)}"

# Layout
app.layout = html.Div(style={'backgroundColor': '#f5f5f5', 'color': 'black', 'textAlign': 'center', 'padding': '20px'}, children=[
    html.H1("Real-Time Monitoring Dashboard", id='title', style={'color': '#333'}),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    
    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px'}, children=[
        html.Div([
            html.H3("CPU Usage", style={'color': '#007bff'}),
            dcc.Graph(id='cpu-usage-graph')
        ]),
        
        html.Div([
            html.H3("Memory Usage", style={'color': '#dc3545'}),
            dcc.Graph(id='memory-usage-graph')
        ]),
        
        html.Div([
            html.H3("Network Utilization", style={'color': '#28a745'}),
            dcc.Graph(id='network-usage-graph')
        ]),
        
        html.Div([
            html.H3("Disk Usage", style={'color': '#ffc107'}),
            dcc.Graph(id='disk-usage-graph')
        ])
    ]),
    
    html.H3("Running Processes"),
    html.Div(id='process-table-container', children=[
        html.Table(id='process-table', style={
            'width': '100%', 'borderCollapse': 'collapse', 'textAlign': 'center',
            'backgroundColor': '#f9f9f9', 'borderRadius': '10px', 'padding': '10px',
            'boxShadow': '2px 2px 10px rgba(0,0,0,0.1)'
        })
    ]),
    html.Button("Show More", id='show-more-btn', n_clicks=0),
    
    html.Div([
        html.H4("Kill Process by PID"),
        dcc.Input(id='pid-input', type='number', placeholder='Enter PID', style={'marginRight': '10px'}),
        html.Button("Kill", id='kill-btn', n_clicks=0, style={'backgroundColor': 'red', 'color': 'white'}),
        html.Div(id='kill-status', style={'marginTop': '10px', 'color': 'red'})
    ], style={'marginTop': '20px'}),
    
    dcc.Store(id='dark-mode-store', storage_type='local'),
    dcc.Store(id='show-more-store', storage_type='memory', data=False)
])

@app.callback(
    [Output('cpu-usage-graph', 'figure'),
     Output('memory-usage-graph', 'figure'),
     Output('network-usage-graph', 'figure'),
     Output('disk-usage-graph', 'figure'),
     Output('process-table', 'children'),
     Output('show-more-store', 'data')],
    [Input('interval-component', 'n_intervals'), Input('show-more-btn', 'n_clicks')],
    [State('show-more-store', 'data')]
)
def update_dashboard(n, show_more_clicks, show_all):
    update_metrics()
    show_all = not show_all if show_more_clicks else show_all
    displayed_processes = process_list[:20] if not show_all else process_list
    
    def create_figure(title, data, color):
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=list(data), mode='lines', name=title, line=dict(color=color)))
        fig.update_layout(title=title, xaxis_title='Time', yaxis_title='Usage (%)')
        return fig
    
    table_header = html.Tr([html.Th("PID"), html.Th("Name"), html.Th("CPU (%)"), html.Th("Memory (MB)")])
    table_rows = [html.Tr([html.Td(pid), html.Td(name), html.Td(f"{cpu:.1f}"), html.Td(f"{mem:.1f}")]) for pid, name, cpu, mem in displayed_processes]
    
    return (
        create_figure("CPU Usage", cpu_history, '#007bff'),
        create_figure("Memory Usage", memory_history, '#dc3545'),
        create_figure("Network Utilization", network_usage, '#28a745'),
        create_figure("Disk Usage", disk_usage, '#ffc107'),
        [table_header] + table_rows,
        show_all
    )

@app.callback(
    Output('kill-status', 'children'),
    [Input('kill-btn', 'n_clicks')],
    [State('pid-input', 'value')]
)
def kill_selected_process(n_clicks, pid):
    if n_clicks > 0 and pid:
        return kill_process(pid)
    return ""

if __name__ == '__main__':
    app.run(debug=True)
