import psutil
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import collections
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Required for deployment

# Store historical data (Max length = 30 readings)
cpu_history = collections.deque(maxlen=30)
memory_history = collections.deque(maxlen=30)
disk_history = collections.deque(maxlen=30)
net_history = collections.deque(maxlen=30)
process_list = []

def update_metrics():
    """Fetch system metrics and update process list."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        net_io = psutil.net_io_counters()
        net_usage = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # Convert to MB

        # Append data to history
        cpu_history.append(cpu_percent)
        memory_history.append(memory_percent)
        disk_history.append(disk_percent)
        net_history.append(net_usage)

        logger.debug(f"CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%, Network: {net_usage} MB")

        # Update process list
        global process_list
        process_list = []
        for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                info = p.as_dict(attrs=['pid', 'name', 'cpu_percent', 'memory_info'])
                process_list.append((
                    info['pid'],
                    info['name'],
                    info['cpu_percent'],
                    info['memory_info'].rss / (1024 * 1024)  # Convert to MB
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage
        process_list.sort(key=lambda x: x[2], reverse=True)
        logger.debug(f"Process list updated with {len(process_list)} processes")

    except Exception as e:
        logger.error(f"Error in update_metrics: {str(e)}")

# Layout
app.layout = html.Div([
    dcc.Store(id='dark-mode-store', data=False),  # Store dark mode state
    html.Button("Toggle Dark Mode", id='dark-mode-toggle', n_clicks=0),
    html.H1("System Performance Dashboard"),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),  # Refresh every 2s
    
    html.Div(id='main-container', children=[
        dcc.Graph(id='cpu-usage-graph'),
        dcc.Graph(id='memory-usage-graph'),
        dcc.Graph(id='disk-usage-graph'),
        dcc.Graph(id='net-usage-graph')
    ]),

    html.Div([
        html.H3("Running Processes"),
        dash_table.DataTable(id='process-table', columns=[
            {"name": "PID", "id": "pid"},
            {"name": "Name", "id": "name"},
            {"name": "CPU (%)", "id": "cpu_percent"},
            {"name": "Memory (MB)", "id": "memory_mb"},
        ], page_size=10)
    ]),
], id='page-content')

# Dark mode toggle callback
@app.callback(
    Output('page-content', 'className'),
    Output('dark-mode-store', 'data'),
    Input('dark-mode-toggle', 'n_clicks'),
    Input('dark-mode-store', 'data')
)
def toggle_dark_mode(n_clicks, dark_mode):
    """Toggle dark mode on button click."""
    dark_mode = not dark_mode if n_clicks else dark_mode
    return ('dark-mode' if dark_mode else '', dark_mode)

# Callback to update graphs & process table
@app.callback(
    [
        Output('cpu-usage-graph', 'figure'),
        Output('memory-usage-graph', 'figure'),
        Output('disk-usage-graph', 'figure'),
        Output('net-usage-graph', 'figure'),
        Output('process-table', 'data')
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Updates dashboard graphs and process table."""
    logger.debug(f"Dashboard update triggered: Interval {n}")

    # Fetch system metrics
    update_metrics()

    def create_figure(title, data, color, yaxis_title):
        """Creates a Plotly figure."""
        return go.Figure(
            data=[go.Scatter(y=list(data), mode='lines', name=title, line=dict(color=color))],
            layout=go.Layout(title=title, xaxis_title='Time', yaxis_title=yaxis_title, template='plotly_white')
        )

    # Process table data
    table_data = [
        {'pid': pid, 'name': name, 'cpu_percent': f"{cpu:.1f}", 'memory_mb': f"{mem:.1f}"}
        for pid, name, cpu, mem in process_list
    ]

    return (
        create_figure("CPU Usage", cpu_history, '#007bff', 'Usage (%)'),
        create_figure("Memory Usage", memory_history, '#dc3545', 'Usage (%)'),
        create_figure("Disk Usage", disk_history, '#1E90FF', 'Usage (%)'),
        create_figure("Network Usage", net_history, '#8A2BE2', 'Data (MB)'),
        table_data
    )

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8060)  # Use port 8060 to avoid conflicts
