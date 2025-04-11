from typing import Generic, TypeVar, List, Optional, Type, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel

from backend.database.base_class import Base
from backend.database.utils import transaction_scope, db_error_handler


# Type variables for the generics
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Base service class with common CRUD operations.
    
    This generic class provides standard create, read, update, and delete
    operations for a SQLAlchemy model.
    
    Type Parameters:
        ModelType: The SQLAlchemy model type
        CreateSchemaType: The Pydantic model for creation operations
        UpdateSchemaType: The Pydantic model for update operations
        ResponseSchemaType: The Pydantic model for responses
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the service with the SQLAlchemy model class.
        
        Args:
            model: The SQLAlchemy model class
        """
        self.model = model
    
    @db_error_handler
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: SQLAlchemy database session
            id: Record ID
            
        Returns:
            The record if found, None otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    @db_error_handler
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    @db_error_handler
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: SQLAlchemy database session
            obj_in: Data for the new record
            
        Returns:
            The created record
        """
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @db_error_handler
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: SQLAlchemy database session
            db_obj: Existing database object to update
            obj_in: New data to update the record with
            
        Returns:
            The updated record
        """
        # If obj_in is a dict, use it directly
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Otherwise convert Pydantic model to dict, excluding unset values
            update_data = obj_in.dict(exclude_unset=True)
        
        # Update the model attributes
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @db_error_handler
    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Remove a record.
        
        Args:
            db: SQLAlchemy database session
            id: ID of the record to remove
            
        Returns:
            The removed record
            
        Raises:
            HTTPException: If the record doesn't exist
        """
        obj = db.query(self.model).get(id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {id} not found"
            )
        db.delete(obj)
        db.commit()
        return obj 