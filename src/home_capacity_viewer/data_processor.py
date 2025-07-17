import pandas as pd
from typing import Dict, Tuple

class DataProcessor:
    def __init__(self, water_data: pd.DataFrame, energy_data: pd.DataFrame):
        """
        Initialize the data processor with water and energy dataframes.
        
        Args:
            water_data (pd.DataFrame): Raw water supply data
            energy_data (pd.DataFrame): Raw energy supply data
        """
        self.water_data = water_data.copy()
        self.energy_data = energy_data.copy()
        
    def process_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process both dataframes and add derived columns.
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Processed water and energy dataframes
        """
        # Calculate home capacity - this needs to be done before processing the water and energy data as it needs the raw water data
        self._process_home_capacity()
    
        # Process water data
        self._process_water_data()
        
        # Process energy data
        self._process_energy_data()
        
        return self.water_data, self.energy_data, self.home_capacity

    
    def _process_water_data(self):
        """Process water data and add derived columns."""
        # Get year columns
        year_cols = [col for col in self.water_data.columns if col not in ['LAD24CD', 'LAD24NM']]
        
        # Calculate trends and changes using original numeric values
        self.water_data['water_trend'] = self.water_data.apply(
            lambda row: self._calculate_trend(row, year_cols), axis=1
        )
        
        self.water_data['water_change_5yr'] = self.water_data.apply(
            lambda row: self._calculate_change(row, year_cols, 5), axis=1
        )
        
        # Calculate summary statistics using original numeric values
        self.water_data['water_avg'] = self.water_data[year_cols].mean(axis=1)
        self.water_data['water_std'] = self.water_data[year_cols].std(axis=1)
        self.water_data['water_max'] = self.water_data[year_cols].max(axis=1)
        self.water_data['water_min'] = self.water_data[year_cols].min(axis=1)
        
        # Convert values to risk levels after calculations
        for year in year_cols:
            self.water_data[year] = self.water_data[year].apply(
                lambda x: self._get_water_risk_level(x)
            )
        
        # Convert summary statistics to risk levels
        self.water_data['water_avg'] = self.water_data['water_avg'].apply(
            lambda x: self._get_water_risk_level(x)
        )
        self.water_data['water_max'] = self.water_data['water_max'].apply(
            lambda x: self._get_water_risk_level(x)
        )
        self.water_data['water_min'] = self.water_data['water_min'].apply(
            lambda x: self._get_water_risk_level(x)
        )
        
        # Rename columns to reflect new meaning
        self.water_data = self.water_data.rename(columns={
            'water_trend': 'risk_trend',
            'water_change_5yr': 'risk_change_5yr',
            'water_avg': 'risk_avg',
            'water_std': 'risk_std',
            'water_max': 'risk_max',
            'water_min': 'risk_min'
        })
    
    def _process_energy_data(self):
        """Process energy data and add derived columns."""
        # Get year columns
        year_cols = [col for col in self.energy_data.columns if col not in ['LAD24CD', 'LAD24NM']]
        
        # Add trend columns
        self.energy_data['energy_trend'] = self.energy_data.apply(
            lambda row: self._calculate_trend(row, year_cols), axis=1
        )
        
        # Add change columns
        self.energy_data['energy_change_5yr'] = self.energy_data.apply(
            lambda row: self._calculate_change(row, year_cols, 5), axis=1
        )
        
        # Add summary statistics
        self.energy_data['energy_avg'] = self.energy_data[year_cols].mean(axis=1)
        self.energy_data['energy_std'] = self.energy_data[year_cols].std(axis=1)
        self.energy_data['energy_max'] = self.energy_data[year_cols].max(axis=1)
        self.energy_data['energy_min'] = self.energy_data[year_cols].min(axis=1)
        
        # Rename columns to reflect new meaning
        self.energy_data = self.energy_data.rename(columns={
            'energy_trend': 'homes_trend',
            'energy_change_5yr': 'homes_change_5yr',
            'energy_avg': 'homes_avg',
            'energy_std': 'homes_std',
            'energy_max': 'homes_max',
            'energy_min': 'homes_min'
        })


    def _process_home_capacity(self) -> pd.DataFrame:

        year_cols = [col for col in self.water_data.columns if col not in ['LAD24CD', 'LAD24NM']]
        binary_water_table = self.water_data[year_cols].map(lambda x: 1 if x > 0 else 0)
        filtered_energy_table = self.energy_data[year_cols].map(lambda x: x if x > 0 else 0)

        home_capacity = binary_water_table[year_cols] * filtered_energy_table[year_cols]
        home_capacity = pd.concat([self.water_data[['LAD24CD', 'LAD24NM']], home_capacity], axis=1)

        self.home_capacity = home_capacity

    
    def _calculate_trend(self, row: pd.Series, year_cols: list) -> str:
        """Calculate the trend of values over time."""
        # Get all values
        values = [row[year] for year in year_cols]
        
        if len(values) < 2:
            return "insufficient data"
        
        # Calculate changes between consecutive years
        changes = [values[i+1] - values[i] for i in range(len(values)-1)]
        
        # Calculate average change
        avg_change = sum(changes) / len(changes)
        
        if avg_change > 0.1:
            return "improving"  # Moving toward more positive values
        elif avg_change < -0.1:
            return "deteriorating"  # Moving toward more negative values
        else:
            return "stable"
    
    def _calculate_change(self, row: pd.Series, year_cols: list, years: int) -> float:
        """Calculate the percentage change over a specified number of years."""
        if len(year_cols) < years + 1:
            return 0.0
        
        start_year = year_cols[0]
        end_year = year_cols[years]
        
        start_value = float(row[start_year])
        end_value = float(row[end_year])
        
        # Handle the case where we're moving from deficit to surplus or vice versa
        if (start_value < 0 and end_value > 0) or (start_value > 0 and end_value < 0):
            # Calculate absolute change in position relative to zero
            return ((end_value - start_value) / abs(start_value)) * 100
            
        return ((end_value - start_value) / abs(start_value)) * 100
    
    def _get_water_risk_level(self, value: float) -> str:
        """Convert water value to risk level for new home construction."""
        if value > 1:
            return "High capacity"
        elif value > 0:
            return "Low capacity"
        elif value > -1:
            return "Low risk deficit"
        else:
            return "High risk deficit" 