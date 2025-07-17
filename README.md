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

Create a `.env` file in the root directory. You must specify which model provider to use:

#### Option A: OpenAI API
```
MODEL_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-4
```

#### Option B: Azure OpenAI
```
MODEL_PROVIDER=azure
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_MODEL=your_model_name  # Optional, defaults to gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview  # Optional, defaults to 2024-02-15-preview
```

**Note**: The `MODEL_PROVIDER` environment variable is required and must be set to either `'openai'` or `'azure'`. The application will validate that all required environment variables for the selected provider are present.

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
- OpenAI/Azure OpenAI for natural language processing 