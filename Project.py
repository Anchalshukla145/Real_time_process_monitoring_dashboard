import psutil
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import collections

# Initialize Dash app
app = dash.Dash(__name__)

# Store historical data
cpu_history = collections.deque(maxlen=20)
memory_history = collections.deque(maxlen=20)

def update_metrics():
    cpu_history.append(psutil.cpu_percent())
    memory_history.append(psutil.virtual_memory().percent)

# Layout with light theme
app.layout = html.Div(style={'backgroundColor': '#f5f5f5', 'color': 'black', 'textAlign': 'center', 'padding': '20px'}, children=[
    html.H1("System Performance Dashboard", style={'color': '#333'}),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    
    html.Div(style={'display': 'flex', 'justifyContent': 'space-around'}, children=[
        html.Div([
            html.H3("CPU Usage", style={'color': '#007bff'}),
            dcc.Graph(id='cpu-usage-graph')
        ], style={'width': '45%'}),

        html.Div([
            html.H3("Memory Usage", style={'color': '#dc3545'}),
            dcc.Graph(id='memory-usage-graph')
        ], style={'width': '45%'})
    ])
])

# Callbacks to update graphs
@app.callback(
    [Output('cpu-usage-graph', 'figure'),
     Output('memory-usage-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    update_metrics()
    
    def create_figure(title, data, color):
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=list(data), mode='lines', name=title, line=dict(color=color)))
        fig.update_layout(title=title, xaxis_title='Time', yaxis_title='Usage (%)',
                          plot_bgcolor='#ffffff', paper_bgcolor='#f5f5f5', font=dict(color='black'))
        return fig
    
    return (
        create_figure("CPU Usage", cpu_history, '#007bff'),
        create_figure("Memory Usage", memory_history, '#dc3545')
    )

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
