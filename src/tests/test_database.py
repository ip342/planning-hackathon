#!/usr/bin/env python3
"""
Test script to verify database creation and functionality with real data
"""

import sys
import os
sys.path.append('src')

from home_capacity_viewer.database import DatabaseManager
from home_capacity_viewer.data_processor import DataProcessor
import pandas as pd

def test_database_creation():
    """Test that the database can be created successfully"""
    print("Testing database creation...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager("sqlite:///test_home_capacity.db")
        
        # Create tables
        db_manager.create_tables()
        print("✅ Database tables created successfully!")
        
        # Test session creation
        session = db_manager.get_session()
        print("✅ Database session created successfully!")
        session.close()
        
        return db_manager
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return None

def test_data_loading():
    """Test that real data can be loaded into the database"""
    print("\nTesting data loading with real CSV data...")
    
    try:
        # Load actual CSV data
        water_csv_path = 'src/data/LA_water_output.csv'
        energy_csv_path = 'src/data/LA_energy_output.csv'
        
        if not os.path.exists(water_csv_path):
            print(f"❌ Water CSV file not found: {water_csv_path}")
            return False
            
        if not os.path.exists(energy_csv_path):
            print(f"❌ Energy CSV file not found: {energy_csv_path}")
            return False
        
        print(f"✅ Found water CSV: {water_csv_path}")
        print(f"✅ Found energy CSV: {energy_csv_path}")
        
        # Load CSV data
        water_output_csv = pd.read_csv(water_csv_path)
        energy_output_csv = pd.read_csv(energy_csv_path)
        
        print(f"✅ Loaded water data: {len(water_output_csv)} rows")
        print(f"✅ Loaded energy data: {len(energy_output_csv)} rows")
        
        # Process data for database (keep as floats)
        processor = DataProcessor(water_output_csv, energy_output_csv)
        processed_water_data, processed_energy_data, processed_home_capacity = processor.process_data(convert_water_to_risk_level=False)
        
        print(f"✅ Processed water data: {len(processed_water_data)} rows")
        print(f"✅ Processed energy data: {len(processed_energy_data)} rows")
        print(f"✅ Processed home capacity data: {len(processed_home_capacity)} rows")
        
        # Initialize database
        db_manager = DatabaseManager("sqlite:///test_loading.db")
        db_manager.create_tables()
        
        # Load processed data into database
        db_manager.load_water_data(processed_water_data)
        db_manager.load_energy_data(processed_energy_data)
        db_manager.load_home_capacity_data(processed_home_capacity)
        
        print("✅ All data loaded successfully into database!")
        
        # Test basic queries
        from home_capacity_viewer.database import WaterData, EnergyData, HomeCapacityData
        session = db_manager.get_session()
        water_count = session.query(WaterData).count()
        energy_count = session.query(EnergyData).count()
        capacity_count = session.query(HomeCapacityData).count()
        session.close()
        
        print(f"✅ Database contains {water_count} water records")
        print(f"✅ Database contains {energy_count} energy records")
        print(f"✅ Database contains {capacity_count} home capacity records")
        
        # Clean up
        if os.path.exists("test_loading.db"):
            os.remove("test_loading.db")
            print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """Test that data processing works correctly"""
    print("\nTesting data processing...")
    
    try:
        # Load actual CSV data
        water_output_csv = pd.read_csv('src/data/LA_water_output.csv')
        energy_output_csv = pd.read_csv('src/data/LA_energy_output.csv')
        
        # Test processing with risk levels (for app display)
        processor1 = DataProcessor(water_output_csv, energy_output_csv)
        water_with_risk, energy_data, home_capacity = processor1.process_data(convert_water_to_risk_level=True)
        
        # Check that water data has risk level strings
        sample_water_value = water_with_risk.iloc[0]['2025']
        if isinstance(sample_water_value, str):
            print(f"✅ Water data converted to risk levels: {sample_water_value}")
        else:
            print(f"❌ Water data not converted to risk levels: {sample_water_value}")
            return False
        
        # Test processing without risk levels (for database) - use fresh processor
        processor2 = DataProcessor(water_output_csv, energy_output_csv)
        water_without_risk, energy_data, home_capacity = processor2.process_data(convert_water_to_risk_level=False)
        
        # Check that water data has float values
        sample_water_value = water_without_risk.iloc[0]['2025']
        if isinstance(sample_water_value, (int, float)):
            print(f"✅ Water data kept as floats: {sample_water_value}")
        else:
            print(f"❌ Water data not kept as floats: {sample_water_value}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Database Functionality with Real Data\n")
    
    tests = [
        test_database_creation,
        test_data_processing,
        test_data_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is working correctly with real data.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 