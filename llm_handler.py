from typing import Dict, Any, Optional
import pandas as pd
from openai import AzureOpenAI
from settings import (
    AZURE_OPENAI_MODEL,
    OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY
)
from data_processor import DataProcessor

class LLMQueryHandler:
    def __init__(self, water_data: pd.DataFrame, energy_data: pd.DataFrame):
        """
        Initialize the LLM query handler with the data sources.
        
        Args:
            water_data (pd.DataFrame): DataFrame containing water supply data
            energy_data (pd.DataFrame): DataFrame containing energy supply data
        """
        # Process the data first
        processor = DataProcessor(water_data, energy_data)
        self.water_data, self.energy_data = processor.process_data()
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_version=OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_MODEL,
            api_key=AZURE_OPENAI_KEY,
        )
        
    def process_query(self, query: str) -> str:
        """
        Process a user query and generate a response using Azure OpenAI.
        
        Args:
            query (str): The user's text query
            year (int): The currently selected year
            
        Returns:
            str: The generated response
        """
        if not query:
            return "Please enter a question about the water or energy supply data."
            
        # Prepare the context with data for all years
        context = self._prepare_context()
        
        # Create the system message with context
        system_message = f"""You are a helpful assistant that answers questions about water supply risk levels and potential new home construction in the UK.
        You have access to the following data for all years:
        
        New homes capability based on water supply risk levels:
        {context['water']}
        
        New homes capability based on energy surplus/deficit:
        {context['energy']}

        Please provide accurate and concise answers based on this data.
        When discussing trends or changes, consider the full range of available years.
        You can also discuss:
        - Trends (improving, deteriorating, or stable)
        - 5-year percentage changes
        - Risk level changes over time
        
        Note: 
        - Water supply data is categorized into risk levels based on the value:
          * High capacity (>1): Sufficient water for new homes
          * Low capacity (0-1): Limited water availability
          * Low risk deficit (-1 to 0): Minor water deficit
          * High risk deficit (<-1): Significant water deficit
        - Positive values indicate water capacity for new homes
        - Negative values indicate water deficit
        - Energy data has been converted to represent the number of new homes that could be built
          based on the energy surplus/deficit in each region (each unit of energy surplus/deficit = 0.1 new homes).
          
          Make your answer incredibly concise. Only respond with boroughs names, values and trends. """
        
        try:
            # Make the API call
            completion = self.client.chat.completions.create(
                model=AZURE_OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Sorry, I encountered an error while processing your query: {str(e)}"
    
    def _prepare_context(self) -> Dict[str, str]:
        """Prepare context data for all years."""
        # Get all year columns (excluding LAD24CD and LAD24NM)
        water_years = [col for col in self.water_data.columns if col not in ['LAD24CD', 'LAD24NM', 'risk_trend', 'risk_change_5yr', 'risk_avg', 'risk_std', 'risk_max', 'risk_min']]
        energy_years = [col for col in self.energy_data.columns if col not in ['LAD24CD', 'LAD24NM', 'homes_trend', 'homes_change_5yr', 'homes_avg', 'homes_std', 'homes_max', 'homes_min']]
        
        # Prepare water data context
        water_context = []
        for _, row in self.water_data.iterrows():
            region_data = []
            for year in water_years:
                value = row[year]
                if value != "No data":  # Skip missing data
                    region_data.append(f"{year}: {value}")
            if region_data:  # Only include regions with data
                water_context.append(
                    f"{row['LAD24NM']}:\n"
                    f"  Risk Levels: {' | '.join(region_data)}\n"
                    f"  Trend: {row['risk_trend']}\n"
                    f"  5-year change: {row['risk_change_5yr']:.1f}%\n"
                    f"  Average Risk: {row['risk_avg']}\n"
                    f"  Risk Range: {row['risk_min']} to {row['risk_max']}"
                )
        
        # Prepare energy data context (now representing new homes)
        energy_context = []
        for _, row in self.energy_data.iterrows():
            region_data = []
            for year in energy_years:
                value = row[year]
                if value != 1000:  # Skip missing data
                    region_data.append(f"{year}: {value:.0f} homes")
            if region_data:  # Only include regions with data
                energy_context.append(
                    f"{row['LAD24NM']}:\n"
                    f"  Potential New Homes: {' | '.join(region_data)}\n"
                    f"  Trend: {row['homes_trend']}\n"
                    f"  5-year change: {row['homes_change_5yr']:.1f}%\n"
                    f"  Average: {row['homes_avg']:.0f} homes\n"
                    f"  Range: {row['homes_min']:.0f} to {row['homes_max']:.0f} homes"
                )
        
        return {
            'water': '\n'.join(water_context) if water_context else "No water risk data available.",
            'energy': '\n'.join(energy_context) if energy_context else "No new homes data available."
        }
    
    def _get_highest_value(self, data: pd.DataFrame, year: int, data_type: str) -> str:
        """Get the region with the highest value for the given year."""
        year_col = str(year)
        if year_col not in data.columns:
            return f"No data available for {year}"
            
        max_idx = data[year_col].idxmax()
        max_value = data.loc[max_idx, year_col]
        region = data.loc[max_idx, 'LAD24NM']
        
        return f"The highest {data_type} supply in {year} is in {region} with a value of {max_value:.2f}"
    
    def _get_lowest_value(self, data: pd.DataFrame, year: int, data_type: str) -> str:
        """Get the region with the lowest value for the given year."""
        year_col = str(year)
        if year_col not in data.columns:
            return f"No data available for {year}"
            
        min_idx = data[year_col].idxmin()
        min_value = data.loc[min_idx, year_col]
        region = data.loc[min_idx, 'LAD24NM']
        
        return f"The lowest {data_type} supply in {year} is in {region} with a value of {min_value:.2f}"
    
    def _get_average_value(self, data: pd.DataFrame, year: int, data_type: str) -> str:
        """Get the average value for the given year."""
        year_col = str(year)
        if year_col not in data.columns:
            return f"No data available for {year}"
            
        avg_value = data[year_col].mean()
        
        return f"The average {data_type} supply in {year} is {avg_value:.2f}" 