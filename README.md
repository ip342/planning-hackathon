# UK Map Dashboard

An interactive dashboard for visualising and analysing water and energy supply data across UK Local Authority Districts.

## Setup Instructions

### 1. Install uv (if not already installed)

```bash
# Install uv using pip
pip install uv

# Or install using curl (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Dependencies

```bash
# Install all required packages using uv (creates virtual environment automatically)
uv sync
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
uv run python -m home_capacity_viewer.app
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
- `src/data/LA_water_output.csv`: Water supply data
- `src/data/LA_energy_output.csv`: Energy supply data

## Requirements

- Python 3.12 or higher
- uv package manager (recommended) or pip

## Dependencies

Key dependencies include:
- Dash and Dash Bootstrap Components for the web interface
- Dash Leaflet for map visualization
- Pandas for data processing
- OpenAI/Azure OpenAI for natural language processing 