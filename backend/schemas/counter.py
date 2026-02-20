from pydantic import BaseModel, Field


class Counter(BaseModel):
    current_number: int = Field(0, alias="current")
    step: int

    class Config:
        from_attributes = True
        validate_by_name = True
        populate_by_name = True
