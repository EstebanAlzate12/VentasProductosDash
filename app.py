import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# --- CARGAR Y LIMPIAR LOS DATOS ---
df = pd.read_csv('monthly_sales_data.csv')  # Asegúrate de que esté en la misma carpeta

# Convertir fechas automáticamente
df['Order Date'] = pd.to_datetime(df['Order Date'], format='mixed', errors='coerce')

# Convertir a números y manejar errores
df['Quantity Ordered'] = pd.to_numeric(df['Quantity Ordered'], errors='coerce')
df['Price Each'] = pd.to_numeric(df['Price Each'], errors='coerce')

# Eliminar filas con datos inválidos
df.dropna(subset=['Order Date', 'Quantity Ordered', 'Price Each'], inplace=True)

# Crear columnas auxiliares
df['Sales'] = df['Quantity Ordered'] * df['Price Each']
df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
df['City'] = df['Purchase Address'].apply(lambda x: x.split(',')[1].strip() if isinstance(x, str) else 'Desconocido')

# --- INICIALIZAR APP ---
app = dash.Dash(__name__)
server = app.server

# --- DISEÑO ---
app.layout = html.Div([
    html.H1("Tablero de Ventas", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.H3("Ventas Mensuales"),
            dcc.Graph(id='line-chart'),
            dcc.RangeSlider(
                id='month-slider',
                min=0,
                max=len(df['Month'].unique()) - 1,
                value=[0, len(df['Month'].unique()) - 1],
                marks={i: m for i, m in enumerate(sorted(df['Month'].unique()))},
                step=None
            )
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Cantidad por Producto"),
            dcc.Dropdown(
                id='product-dropdown',
                options=[{'label': p, 'value': p} for p in df['Product'].unique()],
                value=df['Product'].unique()[0]
            ),
            dcc.Graph(id='bar-chart'),
        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
    ]),

    html.Div([
        html.Div([
            html.H3("Participación de Ventas por Ciudad"),
            html.Button("Cambiar Fondo", id='pie-btn', n_clicks=0),
            dcc.Graph(id='pie-chart')
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Dispersión Precio vs. Cantidad"),
            dcc.RadioItems(
                id='scatter-type',
                options=[
                    {'label': 'Dispersión', 'value': 'scatter'},
                    {'label': 'Burbuja', 'value': 'bubble'},
                ],
                value='scatter',
                inline=True
            ),
            dcc.Graph(id='scatter-chart')
        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
    ])
])

# --- CALLBACKS ---

@app.callback(
    Output('line-chart', 'figure'),
    Input('month-slider', 'value')
)
def update_line_chart(month_range):
    months = sorted(df['Month'].unique())
    selected_months = months[month_range[0]:month_range[1]+1]
    filtered = df[df['Month'].isin(selected_months)]
    sales_by_month = filtered.groupby('Month')['Sales'].sum().reset_index()
    fig = px.line(sales_by_month, x='Month', y='Sales', title='Ventas por Mes')
    fig.update_xaxes(rangeslider_visible=True)
    return fig

@app.callback(
    Output('bar-chart', 'figure'),
    Input('product-dropdown', 'value')
)
def update_bar_chart(product):
    filtered = df[df['Product'] == product]
    grouped = filtered.groupby('Month')['Quantity Ordered'].sum().reset_index()
    fig = px.bar(grouped, x='Month', y='Quantity Ordered', title=f'Cantidad Vendida: {product}')
    return fig

@app.callback(
    Output('pie-chart', 'figure'),
    Input('pie-btn', 'n_clicks')
)
def update_pie_chart(n_clicks):
    sales_by_city = df.groupby('City')['Sales'].sum().reset_index()
    fig = px.pie(sales_by_city, values='Sales', names='City', title='Ventas por Ciudad')
    if n_clicks % 2 == 1:
        fig.update_layout(paper_bgcolor='lightgray')
    return fig

@app.callback(
    Output('scatter-chart', 'figure'),
    Input('scatter-type', 'value')
)
def update_scatter(chart_type):
    if chart_type == 'scatter':
        fig = px.scatter(df, x='Price Each', y='Quantity Ordered', color='Product',
                         title='Precio vs. Cantidad')
    else:
        fig = px.scatter(df, x='Price Each', y='Quantity Ordered', size='Sales',
                         color='Product', title='Precio vs. Cantidad (Burbujas)')
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
