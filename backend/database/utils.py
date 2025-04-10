from typing import Dict, List, Type, TypeVar, Generic, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session
from datetime import datetime, date

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