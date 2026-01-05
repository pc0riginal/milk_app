from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Annotated
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

class Person(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    email: Optional[str] = None

class PaymentStatus(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    person: str
    month: int
    year: int
    paid: bool = False
    paid_date: Optional[datetime] = None

class Settings(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    milk_rate: float = 60.0  # default rate per liter

class Purchase(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    date: datetime = Field(default_factory=datetime.now)
    person: str  # single person name
    quantity: float  # liters
    price_per_liter: float
    total_cost: float

class PurchaseCreate(BaseModel):
    person: str
    quantity: float
    price_per_liter: Optional[float] = None
    date: Optional[datetime] = None

class DailySummary(BaseModel):
    date: str
    total_quantity: float
    total_cost: float
    purchases: List[Purchase]

class MonthlySummary(BaseModel):
    month: str
    year: int
    total_quantity: float
    total_cost: float
    daily_summaries: List[DailySummary]