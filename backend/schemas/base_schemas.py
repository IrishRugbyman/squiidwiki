from typing import TypeVar, Generic, Optional, List, Type
from pydantic import BaseModel, Field, create_model
from datetime import datetime


class TimeStampMixin(BaseModel):
    """Mixin class that adds timestamp fields to a schema"""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class IDMixin(BaseModel):
    """Mixin class that adds an ID field to a schema"""
    id: int = Field(..., description="Unique identifier")


class ResponseBase(IDMixin, TimeStampMixin, BaseModel):
    """Base class for response schemas with ID and timestamps"""
    class Config:
        orm_mode = True


class PaginatedResponse(BaseModel):
    """
    Base class for paginated response schemas.
    
    This class provides common pagination metadata fields.
    Subclasses should define the 'items' field with the appropriate type.
    """
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    
    class Config:
        orm_mode = True


# Type variables for the schema factory
T = TypeVar('T', bound=BaseModel)
CreateT = TypeVar('CreateT', bound=BaseModel)
UpdateT = TypeVar('UpdateT', bound=BaseModel)
ResponseT = TypeVar('ResponseT', bound=BaseModel)


class SchemaFactory(Generic[T]):
    """
    Factory for creating related schema classes.
    
    This factory creates Create, Update, and Response schemas from a base schema.
    """
    
    @staticmethod
    def create_response_schema(
        base_schema: Type[T], 
        name: str, 
        extra_fields: dict = None
    ) -> Type[ResponseT]:
        """
        Create a response schema from a base schema.
        
        Args:
            base_schema: Base schema class
            name: Name for the new schema class
            extra_fields: Additional fields to add to the schema
            
        Returns:
            New response schema class
        """
        fields = {
            '__annotations__': {
                'id': int,
                'created_at': datetime,
                'updated_at': Optional[datetime]
            }
        }
        
        if extra_fields:
            for field_name, (field_type, field_default) in extra_fields.items():
                fields['__annotations__'][field_name] = field_type
                fields[field_name] = field_default
        
        # Create the model with orm_mode enabled
        return create_model(
            name,
            __base__=(base_schema, ResponseBase),
            **fields
        )
    
    @staticmethod
    def create_update_schema(
        base_schema: Type[T], 
        name: str, 
        optional_fields: list = None
    ) -> Type[UpdateT]:
        """
        Create an update schema from a base schema.
        
        Args:
            base_schema: Base schema class
            name: Name for the new schema class
            optional_fields: Fields to make optional
            
        Returns:
            New update schema class
        """
        # Get field annotations from the base schema
        annotations = getattr(base_schema, '__annotations__', {})
        
        # Make specified fields optional
        fields = {'__annotations__': {}}
        for field_name, field_type in annotations.items():
            if optional_fields and field_name in optional_fields:
                fields['__annotations__'][field_name] = Optional[field_type]
                fields[field_name] = None
        
        # Create the update model
        return create_model(
            name,
            __base__=(BaseModel,),
            **fields
        )


def create_paginated_response(item_schema: Type[BaseModel], name: str) -> Type[BaseModel]:
    """
    Create a paginated response schema for a specific item type.
    
    Args:
        item_schema: Schema class for the items
        name: Name for the new schema class
        
    Returns:
        New paginated response schema class
    """
    return create_model(
        name,
        __base__=(PaginatedResponse,),
        items=(List[item_schema], ...),
    ) 