import psutil
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import collections

# Initialize Dash app
app = dash.Dash(__name__)

# Store historical data for smooth line charts
cpu_history = collections.deque(maxlen=30)
memory_history = collections.deque(maxlen=30)
disk_history = collections.deque(maxlen=30)
net_history = collections.deque(maxlen=30)

# Layout
app.layout = html.Div(id='main-div', children=[
    # Header
    html.H1("Real-Time System Performance Dashboard", id="header", style={'color': '#FFD700', 'textAlign': 'center'}),
    
    # Dark Mode Button
    html.Button("Dark Mode", id="theme-button", n_clicks=0, style={
        "marginTop": "20px", "marginLeft": "50%", "transform": "translateX(-50%)",
        'backgroundColor': '#444', 'color': 'white', 'padding': '10px', 'border': 'none'
    }),
    
    # Update interval
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),  # Update every 2 seconds
    
    # Graph containers
    html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'}, children=[
        html.Div([
            html.H3("CPU Usage", style={'color': '#00FF00', 'textAlign': 'center'}),
            dcc.Graph(id='cpu-usage-graph')
        ], style={'width': '45%'}),

        html.Div([
            html.H3("Memory Usage", style={'color': '#FF4500', 'textAlign': 'center'}),
            dcc.Graph(id='memory-usage-graph')
        ], style={'width': '45%'}),

        html.Div([
            html.H3("Disk Usage", style={'color': '#1E90FF', 'textAlign': 'center'}),
            dcc.Graph(id='disk-usage-graph')
        ], style={'width': '45%'}),

        html.Div([
            html.H3("Network Activity", style={'color': '#8A2BE2', 'textAlign': 'center'}),
            dcc.Graph(id='net-usage-graph')
        ], style={'width': '45%'})
    ]),

    html.H3("Running Processes", style={'color': '#FFD700', 'marginTop': '20px', 'textAlign': 'center'}),
    html.Button("More", id="more-button", n_clicks=0, style={'marginBottom': '10px', 'padding': '10px', 'backgroundColor': '#444', 'color': 'white'}),
    html.Div(id='process-table-container'),

    # Additional Graphs Section
    html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap', 'marginTop': '20px'}, children=[
        # Pie Chart
        html.Div([
            html.H3("System Load Distribution", style={'color': '#FFD700', 'textAlign': 'center'}),
            dcc.Graph(id='pie-chart')
        ], style={'width': '45%'}),

        # Histogram
        html.Div([
            html.H3("CPU Usage Distribution", style={'color': '#FFD700', 'textAlign': 'center'}),
            dcc.Graph(id='histogram')
        ], style={'width': '45%'}),

        # Scatter Plot
        html.Div([
            html.H3("Memory vs CPU Usage", style={'color': '#FFD700', 'textAlign': 'center'}),
            dcc.Graph(id='scatter-plot')
        ], style={'width': '45%'}),

        # Bar Graph
        html.Div([
            html.H3("Disk vs Network Usage", style={'color': '#FFD700', 'textAlign': 'center'}),
            dcc.Graph(id='bar-graph')
        ], style={'width': '45%'})
    ])
])

# Callbacks to update graphs and process table
@app.callback(
    [Output('cpu-usage-graph', 'figure'),
     Output('memory-usage-graph', 'figure'),
     Output('disk-usage-graph', 'figure'),
     Output('net-usage-graph', 'figure'),
     Output('process-table-container', 'children'),
     Output('pie-chart', 'figure'),
     Output('histogram', 'figure'),
     Output('scatter-plot', 'figure'),
     Output('bar-graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('more-button', 'n_clicks'),
     Input('theme-button', 'n_clicks'),
     Input('process-table-container', 'n_clicks')]
)
def update_dashboard(n, more_clicks, theme_button_clicks, kill_clicks):
    # Get system metrics
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    net_usage = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    
    # Define theme based on button clicks
    if theme_button_clicks % 2 == 1:
        background_color = "#1e1e1e"
        text_color = "white"
        button_text = "Light Mode"
        table_bg_color = "#333"  # Dark background for table
        table_text_color = "white"  # Light text for table
    else:
        background_color = "white"
        text_color = "black"
        button_text = "Dark Mode"
        table_bg_color = "#fff"  # Light background for table
        table_text_color = "black"  # Dark text for table
    
    # Update button text dynamically
    app.layout.children[1].children = button_text
    
    # Update system metrics history
    cpu_history.append(cpu_usage)
    memory_history.append(memory_usage)
    disk_history.append(disk_usage)
    net_history.append(net_usage / (1024 * 1024))  # Convert to MB
    
    # CPU Usage Graph
    cpu_fig = go.Figure()
    cpu_fig.add_trace(go.Scatter(y=list(cpu_history), mode='lines', name='CPU Usage', line=dict(color='#00FF00')))
    cpu_fig.update_layout(title='CPU Usage (%)', xaxis_title='Time', yaxis_title='Usage (%)', plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Memory Usage Graph
    memory_fig = go.Figure()
    memory_fig.add_trace(go.Scatter(y=list(memory_history), mode='lines', name='Memory Usage', line=dict(color='#FF4500')))
    memory_fig.update_layout(title='Memory Usage (%)', xaxis_title='Time', yaxis_title='Usage (%)', plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Disk Usage Graph
    disk_fig = go.Figure()
    disk_fig.add_trace(go.Scatter(y=list(disk_history), mode='lines', name='Disk Usage', line=dict(color='#1E90FF')))
    disk_fig.update_layout(title='Disk Usage (%)', xaxis_title='Time', yaxis_title='Usage (%)', plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Network Usage Graph
    net_fig = go.Figure()
    net_fig.add_trace(go.Scatter(y=list(net_history), mode='lines', name='Network Usage (MB)', line=dict(color='#8A2BE2')))
    net_fig.update_layout(title='Network Activity (MB)', xaxis_title='Time', yaxis_title='Data (MB)', plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Process Table
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except psutil.NoSuchProcess:
            continue
    
    processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    
    limit = 20 if more_clicks == 0 else len(processes)
    table_header = ["Process Name", "Process ID", "Memory Usage (%)", "CPU Usage (%)", "Action"]
    table_rows = []
    for proc in processes[:limit]:
        proc_info = [
            proc['name'], 
            proc['pid'], 
            f"{proc['memory_percent']:.2f}", 
            f"{proc['cpu_percent']:.2f}",
            html.Button('Kill', id=f"kill-{proc['pid']}", n_clicks=0, style={'backgroundColor': 'red', 'color': 'white', 'padding': '5px', 'border': 'none'})
        ]
        table_rows.append(proc_info)
    
    process_table = html.Table([ 
        html.Thead(html.Tr([html.Th(col, style={'padding': '10px', 'borderBottom': '2px solid white', 'color': text_color}) for col in table_header])),
        html.Tbody([html.Tr([html.Td(cell, style={'padding': '10px', 'borderBottom': '1px solid gray', 'backgroundColor': table_bg_color, 'color': table_text_color}) for cell in row]) for row in table_rows])
    ], style={'width': '80%', 'margin': 'auto', 'borderCollapse': 'collapse', 'color': text_color})
    
    # Pie Chart (example: system load distribution)
    pie_fig = go.Figure(data=[go.Pie(labels=['CPU', 'Memory', 'Disk', 'Network'], values=[cpu_usage, memory_usage, disk_usage, net_usage / (1024 * 1024)])])
    pie_fig.update_layout(title="System Load Distribution", plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Histogram (example: CPU usage distribution)
    hist_fig = go.Figure(data=[go.Histogram(x=list(cpu_history), nbinsx=10, marker=dict(color='#00FF00'))])
    hist_fig.update_layout(title="CPU Usage Distribution", xaxis_title="CPU Usage (%)", yaxis_title="Frequency", plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Scatter Plot (example: memory vs cpu usage)
    scatter_fig = go.Figure(data=[go.Scatter(x=list(memory_history), y=list(cpu_history), mode='markers', marker=dict(color='#FF4500'))])
    scatter_fig.update_layout(title="Memory vs CPU Usage", xaxis_title="Memory Usage (%)", yaxis_title="CPU Usage (%)", plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))
    
    # Bar Graph (example: disk vs network usage)
    bar_fig = go.Figure(data=[go.Bar(x=['Disk', 'Network'], y=[disk_usage, net_usage / (1024 * 1024)], marker=dict(color=['#1E90FF', '#8A2BE2']))])
    bar_fig.update_layout(title="Disk vs Network Usage", xaxis_title="Resource", yaxis_title="Usage (MB)", plot_bgcolor=background_color, paper_bgcolor=background_color, font=dict(color=text_color))

    return cpu_fig, memory_fig, disk_fig, net_fig, process_table, pie_fig, hist_fig, scatter_fig, bar_fig


if __name__ == '__main__':
    app.run(debug=True)
