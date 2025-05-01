from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import assign
from dash.dependencies import Input, Output, State
import pandas as pd
import requests
from llm_handler import LLMQueryHandler
from data_processor import DataProcessor
# Load GeoJSON data
geojson_url = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_May_2024_Boundaries__UK_BSC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson'
response = requests.get(geojson_url)
geojson_data = response.json()

# Load CSV data
water_output_csv = pd.read_csv('data/LA_water_output.csv')
energy_output_csv = pd.read_csv('data/LA_energy_output.csv')
processor = DataProcessor(water_output_csv, energy_output_csv)
processed_water_data, processed_energy_data = processor.process_data()


# Define colorscale (these colors will be used for both water and energy data)
neg_colors = ['#8B2E23', '#C05746', '#E8998D']  # Reds for negative values
pos_colors = ['#9DC08B', '#609966', '#315C2B', '#254D20', '#1A3D15']  # Greens for positive values
colorscale = neg_colors + pos_colors[1:] + ['#A9A9A9']  # Add grey for missing data

# Function to update GeoJSON data with values for a specific year
def update_geojson_data(year, data_source='water'):
    csv_data = energy_output_csv if data_source == 'energy' else water_output_csv
    
    # Get min and max values for color scaling
    values = []
    for feature in geojson_data['features']:
        lad24cd = feature["properties"]["LAD24CD"]
        try:
            value = csv_data[csv_data["LAD24CD"] == lad24cd][str(year)].values[0]
            values.append(value)
        except:
            pass
    
    global min_val, max_val, classes, colorbar
    min_val = min(values)
    max_val = max(values)
    
    # Update classes
    neg_classes = [min_val, min_val/2, 0]
    pos_classes = [0, max_val/4, max_val/2, max_val*0.75, max_val]
    classes = neg_classes + pos_classes[1:] + [1000]
    
    # Update colorbar categories
    ctg = []
    for i in range(len(neg_classes)-1):
        ctg.append(f"{neg_classes[i]:.1f} to {neg_classes[i+1]:.1f}")
    for i in range(len(pos_classes)-1):
        if i == len(pos_classes)-2:
            ctg.append(f"{pos_classes[i]:.1f}+")
        else:
            ctg.append(f"{pos_classes[i]:.1f} to {pos_classes[i+1]:.1f}")
    ctg.append("No data")
    
    # Update colorbar
    colorbar = dlx.categorical_colorbar(
        categories=ctg,
        colorscale=colorscale,
        width=500,
        height=30,
        position="bottomleft"
    )
    
    # Update feature values
    for feature in geojson_data['features']:
        lad24cd = feature["properties"]["LAD24CD"]
        try:
            value = csv_data[csv_data["LAD24CD"] == lad24cd][str(year)].values[0]
            feature["properties"]["value"] = value
        except:
            feature["properties"]["value"] = 1000
    
    return geojson_data

# Initialize with 2025 water data
geojson_data = update_geojson_data(2025, 'water')

# Define initial classes
values = [feature["properties"]["value"] for feature in geojson_data['features'] if feature["properties"]["value"] != 1000]
min_val = min(values)
max_val = max(values)

# For negative values (red scale)
neg_classes = [min_val, min_val/2, 0]
pos_classes = [0, max_val/4, max_val/2, max_val*0.75, max_val]
classes = neg_classes + pos_classes[1:] + [1000]

# Create initial colorbar
ctg = []
for i in range(len(neg_classes)-1):
    ctg.append(f"{neg_classes[i]:.1f} to {neg_classes[i+1]:.1f}")
for i in range(len(pos_classes)-1):
    if i == len(pos_classes)-2:
        ctg.append(f"{pos_classes[i]:.1f}+")
    else:
        ctg.append(f"{pos_classes[i]:.1f} to {pos_classes[i+1]:.1f}")
ctg.append("No data")

colorbar = dlx.categorical_colorbar(
    categories=ctg,
    colorscale=colorscale,
    width=400,
    height=30,
    position="bottomleft"
)

# Geojson rendering logic
style_handle = assign("""function(feature, context){
    const {classes, colorscale, style, colorProp} = context.hideout;
    const value = feature.properties[colorProp];
    
    if (value === 1000) {
        style.fillColor = colorscale[colorscale.length - 1];  // Use last color (dark grey) for missing data
        return style;
    }
    
    if (value < 0) {  // Handle negative values
        for (let i = 0; i < 3; ++i) {  // 3 is the number of negative classes
            if (value <= classes[i]) {
                style.fillColor = colorscale[i];
                break;
            }
        }
    } else {  // Handle zero and positive values
        for (let i = 3; i < classes.length - 1; ++i) {  // Start from first positive class
            if (value <= classes[i]) {
                style.fillColor = colorscale[i];
                break;
            }
        }
        // If no class matched (value is greater than all class boundaries)
        if (value > classes[classes.length - 2]) {
            style.fillColor = colorscale[classes.length - 2];  // Use the last color before grey
        }
    }
    return style;
}""")

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Initialize LLM query handler
llm_handler = LLMQueryHandler(water_output_csv, energy_output_csv)

# Create info control
def get_info(feature=None, data_source='water'):
    title = "Water Supply Forecast" if data_source == 'water' else "Energy Supply Forecast"
    header = [html.H4(title)]
    if not feature:
        return header + [html.P("Hover over a region")]
    
    value = feature["properties"]["value"]
    value_display = "No data" if value == 1000 else f"{value:.2f}"
    
    return header + [
        html.B(feature["properties"]["LAD24NM"]),
        html.Br(),
        f"Value: {value_display}"
    ]

info = html.Div(
    children=get_info(),
    id="info",
    className="info",
    style={"position": "absolute", "top": "10px", "right": "10px", "zIndex": "1000", "background": "white", "padding": "10px"}
)

# Add data source checkboxes
data_source_checkboxes = html.Div([
    dbc.RadioItems(
        options=[
            {"label": "Water", "value": "water"},
            {"label": "Energy", "value": "energy"}
        ],
        value="water",
        id="data-source-checklist",
        inline=True
    )
], style={"margin": "10px"})

# Map component
map_component = html.Div([
    dl.Map(center=[54.5, -3.4380], zoom=5.4, children=[
        dl.TileLayer(url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'),
        dl.GeoJSON(
            data=geojson_data,
            id="geojson",
            options=dict(style=style_handle),
            hoverStyle=dict(weight=5, color="#666", dashArray=""),
            hideout=dict(
                colorscale=colorscale,
                classes=classes,
                style=dict(weight=2, opacity=1, color="white", dashArray="3", fillOpacity=0.7),
                colorProp="value"
            ),
            children=[dl.Tooltip(id="tooltip")]
        ),
        colorbar,
        info
    ], id="map", style={'height': '620px', 'width': '100%', 'margin': 'auto'}),

    data_source_checkboxes,
    
    dcc.Slider(
        id='time-slider',
        min=min(int(col) for col in water_output_csv.drop(columns=['LAD24CD', 'LAD24NM']).columns),
        max=max(int(col) for col in water_output_csv.drop(columns=['LAD24CD', 'LAD24NM']).columns),
        value=2025,
        marks={str(year): {'label': str(year), 'style': {'transform': 'rotate(45deg)', 'whiteSpace': 'nowrap'}} 
               for year in range(min(int(col) for col in water_output_csv.drop(columns=['LAD24CD', 'LAD24NM']).columns), 
                               max(int(col) for col in water_output_csv.drop(columns=['LAD24CD', 'LAD24NM']).columns) + 1)},
        step=None
    )], style={'padding': '20px'}
)

# Text query component
text_query = html.Div(
    [
        dbc.Input(
            id="text-query",
            placeholder="Ask me a question...",
            type="text",
            debounce=True,  # Add debounce to prevent multiple rapid updates
            n_submit=0,  # Track Enter key presses
        ),
        html.Br(),
        html.P(id="text-output"),
    ],
    style={'padding': '20px'}
)

# Define the layout
app.layout = html.Div([
    dbc.NavbarSimple(
        brand="UK Map Dashboard",
        brand_href="#",
        color="#011638",
        dark=True,
    ),
    dbc.Container([
        dbc.Tabs(
            [
                dbc.Tab(
                    dbc.Row([
                        dbc.Col(map_component, width=12),
                        dbc.Col(text_query, width=12)
                    ], style={'padding': '20px'}),
                    label="Map",
                    tab_id="map-app"
                ),
                dbc.Tab(
                    html.Div([
                        html.H3("Energy Analysis"),
                        html.Div(id="energy-table-container")
                    ], style={'padding': '20px'}),
                    label="Energy",
                    tab_id="tab-energy"
                ),
                dbc.Tab(
                    html.Div([
                        html.H3("Water Analysis"),
                        html.Div(id="water-table-container")
                    ], style={'padding': '20px'}),
                    label="Water",
                    tab_id="tab-water"
                )
            ],
            id="tabs",
            active_tab="map-app",
            style={
                'marginTop': '20px',
                'marginBottom': '20px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'borderRadius': '5px',
                'backgroundColor': 'white'
            }
        )
    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa'})
])

# Callback for info box
@app.callback(
    Output("info", "children"),
    [Input("geojson", "hoverData"),
     Input("data-source-checklist", "value")]
)
def info_hover(feature, data_source):
    return get_info(feature, data_source)

# Callback for tooltip
@app.callback(
    Output("tooltip", "children"),
    [Input("geojson", "hoverData")]
)
def update_tooltip(feature):
    if feature is not None:
        return feature["properties"]["LAD24NM"]
    return None

# Callback to update GeoJSON data based on slider and data source
@app.callback(
    [Output("geojson", "data"),
     Output("map", "children")],  # Add output for map children to update colorbar
    [Input("time-slider", "value"),
     Input("data-source-checklist", "value")]
)
def update_geojson(year, data_source):
    # Update the GeoJSON data
    geojson_data = update_geojson_data(year, data_source)
    
    # Recreate the map with updated colorbar
    map_children = [
        dl.TileLayer(url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'),
        dl.GeoJSON(
            data=geojson_data,
            id="geojson",
            options=dict(style=style_handle),
            hoverStyle=dict(weight=5, color="#666", dashArray=""),
            hideout=dict(
                colorscale=colorscale,
                classes=classes,
                style=dict(weight=2, opacity=1, color="white", dashArray="3", fillOpacity=0.7),
                colorProp="value"
            ),
            children=[dl.Tooltip(id="tooltip")]
        ),
        colorbar,
        info
    ]
    
    return geojson_data, map_children

# Callback to update text output
@app.callback(
    Output('text-output', 'children'),
    Input('text-query', 'n_submit'),  # Trigger on Enter key press
    [State('text-query', 'value')]  # Get the current input value
)
def update_text_output(n_submit, query):
    if n_submit > 0 and query:  # Only execute if Enter was pressed and there's a query
        response = llm_handler.process_query(query)
        # Split response into paragraphs and format with HTML
        paragraphs = response.split('\n\n')
        formatted_response = []
        for p in paragraphs:
            if p.strip():
                # Convert markdown-style formatting to HTML
                p = p.replace('**', '').replace('*', '')  # Remove markdown
                formatted_response.append(html.P(p))
        return formatted_response
    return html.P('Press Enter to submit your question')

# Callback to display energy data table
@app.callback(
    Output('energy-table-container', 'children'),
    Input('tabs', 'active_tab')
)
def display_energy_table(active_tab):
    if active_tab == 'tab-energy':
        return dash_table.DataTable(
            data=processed_energy_data.to_dict('records'),
            columns=[{"name": i, "id": i} for i in processed_energy_data.columns],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': '#011638',
                'color': 'white',
                'fontWeight': 'bold'
            }
        )
    return None

# Callback to display water data table
@app.callback(
    Output('water-table-container', 'children'),
    Input('tabs', 'active_tab')
)
def display_water_table(active_tab):
    if active_tab == 'tab-water':
        return dash_table.DataTable(
            data=processed_water_data.to_dict('records'),
            columns=[{"name": i, "id": i} for i in processed_water_data.columns],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': '#011638',
                'color': 'white',
                'fontWeight': 'bold'
            }
        )
    return None

# Run the app
if __name__ == '__main__':
    app.run(debug=True)