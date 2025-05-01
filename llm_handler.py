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
        self.water_data, self.energy_data, self.home_capacity = processor.process_data()
        
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
        self.system_message = f"""You are an AI assistant communicating water supply and energy data for UK Local Authority Districts.
        This information has been used to also calculate total number of new homes based on water supply risk levels, energy supply surplus/deficit,
        and housing targets for each Local Authority District.

        You have access to the following data for all years:
        
        Water supply risk levels:
        {context['water']}
        
        Home capacity taking into account both energy supply and housing targets:
        {context['energy']}

        Home capacity based on both water supply risk levels and energy supply and housing targets:
        {context['home_capacity']}

        You may have to sum values for different years and across different Local Authority Districts to get a total.

        Water supply data is categorized into risk levels:
        - High capacity (>1): Strong positive value, best for new homes
        - Low capacity (0-1): Weak positive value, limited capacity
        - Low risk deficit (-1 to 0): Small negative value, minor issues
        - High risk deficit (<-1): Large negative value, significant issues

        Energy data shows the energy surplus/deficit per Local Authority District per year when compared to housing targets
        in each year.

        Home capacity is calculated by multiplying the water supply risk level by the energy supply surplus/deficit,
        taking 0.1 as the number of homes per unit of excess energy in MW available. 

        Format your responses using markdown:
        - Use **bold** for important values and trends
        - Use *italics* for emphasis
        - Separate paragraphs with blank lines
        - Use bullet points for lists
        - Use > for important notes or warnings

        Example format:
        **10,000 homes**: The total number of homes that there is capacity for in the UK in 2030. The Local Authority Districta
        with the highest home capacities are *London* (3,500 homes), *Manchester* (2,000 homes), and *Birmingham* (1,500 homes).
    
        ALWAYS start with the exact answer in bold, and explanation below.
        If a question refers to a specific table, use the data from that table.
            (e.g. water utility --> water table,
            energy infrastructure --> energy table,
            building new homes --> home capacity table),
        only use the data from that table.
        Provide accurate and concise answers based on the data, and always quote numbers where you can.
        Explain whether analysis is based on water supply risk levels or energy supply surplus/deficit.
        """

        try:
            # Make the API call
            completion = self.client.chat.completions.create(
                model=AZURE_OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": query}
                ],
                temperature=0.5
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
                    f"  Water Supply Risk Level: {' | '.join(region_data)}\n"
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
                    f"  Energy Supply: {' | '.join(region_data)}\n"
                    f"  Trend: {row['homes_trend']}\n"
                    f"  5-year change: {row['homes_change_5yr']:.1f}%\n"
                    f"  Average: {row['homes_avg']:.0f} homes\n"
                    f"  Range: {row['homes_min']:.0f} to {row['homes_max']:.0f} homes"
                )

        home_capacity_context = []
        for _, row in self.home_capacity.iterrows():
            region_data = []
            for year in self.home_capacity.columns[2:]:
                value = row[year]
                region_data.append(f"{year}: {value:.0f} homes")
            if region_data:  # Only include regions with data
                home_capacity_context.append(
                    f"{row['LAD24NM']}:\n"
                    f"  Home Capacity: {' | '.join(region_data)}\n"
                )
        
        return {
            'water': '\n'.join(water_context) if water_context else "No water risk data available.",
            'energy': '\n'.join(energy_context) if energy_context else "No new homes data available.",
            'home_capacity': '\n'.join(home_capacity_context) if home_capacity_context else "No home capacity data available."
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