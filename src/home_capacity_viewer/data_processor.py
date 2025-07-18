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
        
    def process_data(self, convert_water_to_risk_level: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process both dataframes and add derived columns.
        
        Args:
            convert_water_to_risk_level (bool): If True, convert water values to risk levels. 
                                               If False, keep water values as floats. Defaults to True.
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Processed water and energy dataframes
        """
        # Calculate home capacity - this needs to be done before processing the water data as it needs the raw data
        self._process_home_capacity()
    
        # Categorise water data into risk levels
        if convert_water_to_risk_level:
            self._categorise_water_data()
        
        return self.water_data, self.energy_data, self.home_capacity

    
    def _categorise_water_data(self):
        """Process water data and add derived columns."""
        # Get year columns
        year_cols = [col for col in self.water_data.columns if col not in ['LAD24CD', 'LAD24NM']]
        
        # Convert values to risk levels after calculations if requested
        for year in year_cols:
            self.water_data[year] = self.water_data[year].apply(
                lambda x: self._get_water_risk_level(x)
            )

    def _process_home_capacity(self) -> pd.DataFrame:
        """Process home capacity - this is calculated by assuming that if there is both water and energy supply,
        the home capacity is dictated by the size of the energy supply. Water supply is treated as a 
        probability of water supply (/risk score), and is therefore is only used as a binary variable."""

        year_cols = [col for col in self.water_data.columns if col not in ['LAD24CD', 'LAD24NM']]
        binary_water_table = self.water_data[year_cols].map(lambda x: 1 if x > 0 else 0)
        filtered_energy_table = self.energy_data[year_cols].map(lambda x: x if x > 0 else 0)

        home_capacity = binary_water_table[year_cols] * filtered_energy_table[year_cols]
        home_capacity = pd.concat([self.water_data[['LAD24CD', 'LAD24NM']], home_capacity], axis=1)

        self.home_capacity = home_capacity

    
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