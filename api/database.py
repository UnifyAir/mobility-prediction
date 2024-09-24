from sqlalchemy import create_engine, Column, String, Integer, MetaData, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
import pandas as pd
import os
from typing import List, Dict
from datetime import datetime

# Database URL (SQLite for simplicity)
DATABASE_URL = "sqlite+aiosqlite:///user_trajectory.db"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

# Define the UserTrajectory model
class UserTrajectory(Base):
    __tablename__ = "user_trajectory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    time = Column(Integer, nullable=False)
    cell1 = Column(Integer, nullable=False)
    distance1 = Column(Integer, nullable=False)
    cell2 = Column(Integer, nullable=True)
    distance2 = Column(Integer, nullable=True)
    cell3 = Column(Integer, nullable=True)
    distance3 = Column(Integer, nullable=True)
    cell4 = Column(Integer, nullable=True)
    distance4 = Column(Integer, nullable=True)
    cell5 = Column(Integer, nullable=True)
    distance5 = Column(Integer, nullable=True)

# Add this to your existing models
class UserContext(Base):
    __tablename__ = "user_contexts"
    
    user_id = Column(String, primary_key=True)
    chat_history = Column(String)  # Stores JSON serialized chat history
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# async def initialize_database():
#     """Initialize the database and create tables."""
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

async def initialize_database():
    """Initialize the database and create tables. Load CSV data if the table is empty."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Check if the table is empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserTrajectory).limit(1))
        if not result.scalars().first():
            # Load data from CSV if the table is empty
            csv_file_path = os.path.join("data", "user_trajectory.csv")
            print("csv_file_path", csv_file_path)
            if os.path.exists(csv_file_path):
                # Use Pandas to load the CSV file
                with open(csv_file_path, 'r') as file:
                    data_df = pd.read_csv(file)
                    print("read data_df", len(data_df))

                # Use a synchronous engine for Pandas to_sql
                sync_engine = create_engine("sqlite:///user_trajectory.db")
                data_df.to_sql(
                    name="user_trajectory",
                    con=sync_engine,
                    index=False,
                    if_exists="append",
                )
                print("CSV data loaded into the database.")
            else:
                print(f"CSV file not found at {csv_file_path}.")

async def get_db():
    """Get an async database session."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_user_trajectory_data(user_id: str, timestamp: int, db: AsyncSession) -> str:
    """
    Fetch user trajectory data from database and return as CSV string
    Args:
        user_id: User identifier
        timestamp: Current timestamp to fetch relevant trajectory window
        db: Database session
    """
    # Calculate time window based on input timestamp
    time_window_start = max(0, timestamp - 100)  # Ensure we don't go below 0
    time_window_end = timestamp + 200  # Add buffer for future predictions
    
    result = await db.execute(
        select(UserTrajectory)
        .where(UserTrajectory.user_id == user_id)
        .where(UserTrajectory.time >= time_window_start)
        .where(UserTrajectory.time <= time_window_end)
    )
    trajectories = result.scalars().all()
    
    if trajectories:
        # Convert SQLAlchemy objects to DataFrame
        df = pd.DataFrame([
            {c.name: getattr(trajectory, c.name) 
             for c in UserTrajectory.__table__.columns}
            for trajectory in trajectories
        ])
        
        # Drop id and user_id columns
        df = df.drop(['id', 'user_id'], axis=1)
        
        # Convert all remaining columns to integer
        for col in df.columns:
            df[col] = df[col].astype(int)
            
        return df.to_csv(index=False)
    return ""
