from typing import Any, Dict, List, Union
from bson import ObjectId
from datetime import datetime

def convert_objectid_to_str(data: Any) -> Any:
    """
    Recursively convert all ObjectId instances to strings in a data structure.
    Handles dictionaries, lists, and nested structures.
    
    Args:
        data: The data structure to convert (dict, list, or any other type)
    
    Returns:
        The same data structure with all ObjectId instances converted to strings
    """
    if isinstance(data, dict):
        return {k: convert_objectid_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    return data

def prepare_mongo_response(data: Union[Dict, List]) -> Union[Dict, List]:
    """
    Prepare a MongoDB response for API serialization.
    Converts all ObjectId instances to strings and handles datetime serialization.
    
    Args:
        data: The data to prepare (dict or list)
    
    Returns:
        The prepared data ready for JSON serialization
    """
    return convert_objectid_to_str(data) 