"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# Example schemas (retain for reference)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# App-specific schemas

OperatorType = Literal["Onrole", "Apprentices"]
TestType = Literal["HV", "FT"]

class ProductionEntry(BaseModel):
    operator_name: str
    operator_id: str
    operator_type: OperatorType
    test_type: TestType
    test_station: str
    device_type: str
    production_count: int = Field(..., ge=0)
    timestamp: datetime

class PackingEntry(BaseModel):
    operator_name: str
    device_type: str
    operator_type: OperatorType
    job_type: str
    packing_count: int = Field(..., ge=0)
    timestamp: datetime

class DowntimeEntry(BaseModel):
    operator_name: str
    description: str
    timestamp: datetime
