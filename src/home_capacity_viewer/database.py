from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import pandas as pd

Base = declarative_base()

# Helper function to create year columns
def create_year_columns(start_year=2025, end_year=2050):
    """Create year columns for database models"""
    return {f'year_{year}': Column(Float) for year in range(start_year, end_year + 1)}

class WaterData(Base):
    """SQLAlchemy model for processed water supply data"""
    __tablename__ = 'water_data'
    
    id = Column(Integer, primary_key=True)
    lad24cd = Column(String(10), nullable=False, index=True)
    lad24nm = Column(String(100), nullable=False)
    
    # Add year columns dynamically
    locals().update(create_year_columns())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EnergyData(Base):
    """SQLAlchemy model for processed energy supply data"""
    __tablename__ = 'energy_data'
    
    id = Column(Integer, primary_key=True)
    lad24cd = Column(String(10), nullable=False, index=True)
    lad24nm = Column(String(100), nullable=False)
    
    # Add year columns dynamically
    locals().update(create_year_columns())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class HomeCapacityData(Base):
    """SQLAlchemy model for calculated home capacity data"""
    __tablename__ = 'home_capacity_data'
    
    id = Column(Integer, primary_key=True)
    lad24cd = Column(String(10), nullable=False, index=True)
    lad24nm = Column(String(100), nullable=False)
    
    # Add year columns dynamically
    locals().update(create_year_columns())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class DatabaseManager:
    """Database manager for handling SQLAlchemy operations"""
    
    def __init__(self, db_url: str = "sqlite:///home_capacity_data.db"):
        """Initialize database manager"""
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.year_range = range(2025, 2051)
        
    def create_tables(self):
        """Create all database tables"""
        import os
        
        # Check if database file already exists
        db_file = self.engine.url.database or 'home_capacity_data.db'
        if os.path.exists(db_file):
            print(f"Database file '{db_file}' already exists - using existing database")
            self._data_exists = True
        else:
            print(f"Creating new database: {db_file}")
            self._data_exists = False
            
        Base.metadata.create_all(bind=self.engine)
        print("Database tables created successfully!")
        
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def _create_year_data_dict(self, row: pd.Series, prefix: str = 'year_') -> dict:
        """Create dictionary of year data from DataFrame row"""
        return {f'{prefix}{year}': float(row.get(str(year), 0.0)) for year in self.year_range}
    
    def _load_data_generic(self, df: pd.DataFrame, model_class, additional_fields: dict = None):
        """Generic method to load data into database"""
        session = self.get_session()
        try:
            for _, row in df.iterrows():
                # Base fields
                record_data = {
                    'lad24cd': row['LAD24CD'],
                    'lad24nm': row['LAD24NM'],
                    **self._create_year_data_dict(row)
                }
                
                record = model_class(**record_data)
                session.add(record)
            
            session.commit()
            print(f"Loaded {len(df)} {model_class.__name__} records")
        except Exception as e:
            session.rollback()
            print(f"Error loading {model_class.__name__} data: {e}")
        finally:
            session.close()
        
    def load_data(self, df: pd.DataFrame, data_type: str):
        """Load data into database"""
        if getattr(self, '_data_exists', False):
            print(f"Skipping {data_type} data load - database already exists")
            return
            
        model_map = {
            'water': WaterData,
            'energy': EnergyData,
            'home_capacity': HomeCapacityData
        }
        
        if data_type not in model_map:
            raise ValueError(f"Unknown data type: {data_type}. Use 'water', 'energy', or 'home_capacity'")
            
        self._load_data_generic(df, model_map[data_type])
        print(f"Loaded {len(df)} {data_type} records")
    
 