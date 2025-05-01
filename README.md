# UK Map Dashboard

An interactive dashboard for visualizing and analyzing water and energy supply data across UK Local Authority Districts.

## Setup Instructions

### 1. Create and Activate Conda Environment

```bash
# Create a new conda environment with Python 3.9
conda create -n uk-dashboard python=3.9

# Activate the environment
conda activate uk-dashboard
```

### 2. Install Requirements

```bash
# Install all required packages
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory with your Azure OpenAI credentials:

```
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
```

### 4. Run the Application

```bash
# Make sure you're in the project root directory
python app.py
```

The application will be available at `http://127.0.0.1:8050/` in your web browser.

## Features

- Interactive map visualization of water and energy supply data
- Time-series analysis with year selection
- Natural language query interface for data analysis
- Detailed data tables for both water and energy metrics
- Color-coded risk levels and capacity indicators

## Data Structure

The application uses two main data sources:
- `data/LA_water_output.csv`: Water supply data
- `data/LA_energy_output.csv`: Energy supply data

## Dependencies

Key dependencies include:
- Dash and Dash Bootstrap Components for the web interface
- Dash Leaflet for map visualization
- Pandas for data processing
- Azure OpenAI for natural language processing 