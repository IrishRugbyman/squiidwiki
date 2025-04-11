from typing import Dict, List, Type, TypeVar, Generic, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session
from datetime import datetime, date
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from contextlib import contextmanager

T = TypeVar('T', bound=BaseModel)
M = TypeVar('M', bound=DeclarativeMeta)

def to_dict(obj: Any) -> Dict:
    """
    Convert SQLAlchemy model instance to dictionary.
    Handles date and datetime conversion to ISO format.
    """
    if obj is None:
        return None
        
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        
        # Handle datetime and date values
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
            
        result[column.name] = value
    
    return result


def to_model(data: Dict, model_class: Type[T]) -> T:
    """
    Convert dictionary to Pydantic model instance.
    """
    if data is None:
        return None
        
    return model_class(**data)


def orm_to_pydantic(db_model: Any, pydantic_model: Type[T]) -> T:
    """
    Convert SQLAlchemy model to Pydantic model.
    """
    if db_model is None:
        return None
        
    # Convert ORM model to dict
    model_dict = to_dict(db_model)
    
    # Create Pydantic model from dict
    return to_model(model_dict, pydantic_model)


def orm_list_to_pydantic(db_models: List[Any], pydantic_model: Type[T]) -> List[T]:
    """
    Convert list of SQLAlchemy models to list of Pydantic models.
    """
    if db_models is None:
        return []
        
    return [orm_to_pydantic(model, pydantic_model) for model in db_models]


def pydantic_to_orm(pydantic_model: BaseModel, orm_model_class: Type[M], exclude_unset: bool = False) -> M:
    """
    Convert Pydantic model to SQLAlchemy model.
    
    Args:
        pydantic_model: Pydantic model instance
        orm_model_class: SQLAlchemy model class
        exclude_unset: If True, will only include fields that were explicitly set
    
    Returns:
        SQLAlchemy model instance
    """
    if pydantic_model is None:
        return None
        
    # Convert Pydantic model to dict, excluding unset fields if requested
    model_dict = pydantic_model.dict(exclude_unset=exclude_unset)
    
    # Create SQLAlchemy model from dict
    return orm_model_class(**model_dict)


def get_or_create(
    db: Session, model: Type[M], defaults: Optional[Dict[str, Any]] = None, **kwargs
) -> tuple[M, bool]:
    """
    Get an instance of a model, or create it if it doesn't exist.
    
    Args:
        db: SQLAlchemy session
        model: SQLAlchemy model class
        defaults: Default values for new instances
        **kwargs: Filter criteria for existing instances
        
    Returns:
        Tuple of (instance, created) where created is True if a new instance was created
    """
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
        
    # Create a new instance with the provided kwargs and defaults
    params = kwargs.copy()
    if defaults:
        params.update(defaults)
        
    instance = model(**params)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    
    return instance, True 


@contextmanager
def transaction_scope(db: Session, error_message: str = "Database transaction failed", status_code: int = 500):
    """
    Provide a transactional scope around a series of operations.
    
    This context manager commits changes if no exceptions are raised,
    and rolls back changes if an exception occurs.
    
    Args:
        db: SQLAlchemy database session
        error_message: Custom error message to include with exceptions
        status_code: HTTP status code to use for non-HTTP exceptions
        
    Yields:
        The database session for use within the context
        
    Raises:
        HTTPException: If any error occurs during the transaction
    """
    try:
        yield db
        db.commit()
    except HTTPException as e:
        db.rollback()
        raise  # Re-raise HTTP exceptions as they are already properly formatted
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status_code, detail=f"{error_message}: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status_code, detail=f"{error_message}: {str(e)}")


def db_error_handler(func):
    """
    Decorator for handling database errors in service methods.
    
    Wraps a function with try/except to handle SQLAlchemy errors
    and convert them to HTTPExceptions.
    
    Usage:
        @db_error_handler
        def my_function(db, ...):
            # database operations
    """
    def wrapper(db: Session, *args, **kwargs):
        try:
            return func(db, *args, **kwargs)
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error during database operation: {str(e)}"
            )
    return wrapper


def parse_date_string(date_str: Optional[str], format_str: str = "%Y-%m-%d"):
    """
    Parse a date string into a datetime.date object.
    
    Args:
        date_str: String representing a date (e.g. "2023-01-01")
        format_str: Format string for datetime.strptime
        
    Returns:
        datetime.date object if successful, None if date_str is None
        
    Raises:
        HTTPException: If the date string is invalid
    """
    from datetime import datetime
    
    if not date_str:
        return None
        
    try:
        return datetime.strptime(date_str, format_str).date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Expected format: {format_str}"
        )


# Utility to check if an entity exists
def ensure_exists(db: Session, model_class, entity_id: int, entity_name: str = "Entity"):
    """
    Check if an entity exists in the database.
    
    Args:
        db: SQLAlchemy database session
        model_class: SQLAlchemy model class
        entity_id: ID of the entity to check
        entity_name: Name of the entity type for the error message
        
    Returns:
        The entity if it exists
        
    Raises:
        HTTPException: If the entity doesn't exist
    """
    entity = db.query(model_class).filter(model_class.id == entity_id).first()
    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"{entity_name} with id {entity_id} not found"
        )
    return entity 