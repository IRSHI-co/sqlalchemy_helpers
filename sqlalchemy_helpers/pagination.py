from typing import Generic, TypeVar, Optional
from flask_restx import Model, fields
from marshmallow import fields as ma_fields, Schema
from math import ceil
from flask_restx import reqparse
from flask_restx import inputs



    
def get_paginated_schema(Schema):
    """
    This function generates a Marshmallow schema for paginated responses.

    Args:
        Schema (Schema): The Marshmallow schema of the items to be paginated.

    Returns:
        PaginatedSchema (Schema): A Marshmallow schema for paginated responses. 
        The schema includes fields for the items (using the provided Schema), 
        total count of items, total pages, current page, and boolean fields 
        indicating if there are next or previous pages.
    """
    class PaginatedSchema(Schema):
        items = ma_fields.Nested(Schema, many=True)
        total_count = ma_fields.Integer()
        total_page = ma_fields.Integer()
        current_page = ma_fields.Integer()
        has_next = ma_fields.Boolean()
        has_prev = ma_fields.Boolean()
        
    return PaginatedSchema


def get_paginated_response_model(response_model):
    """
    This function generates a Flask-RESTPlus model for paginated responses.

    Args:
        response_model (Model): The Flask-RESTPlus model of the items to be paginated.

    Returns:
        PaginatedResponseModel (Model): A Flask-RESTPlus model for paginated responses. 
        The model includes fields for the items (using the provided response_model), 
        total count of items, total pages, current page, and boolean fields 
        indicating if there are next or previous pages.
    """
    return Model('PaginatedResponseModel', {
        'items': fields.List(fields.Nested(response_model)),
        'total_count': fields.Integer,
        'total_page': fields.Integer,
        'current_page': fields.Integer,
        'has_next': fields.Boolean,
        'has_prev': fields.Boolean
    })
    
T = TypeVar('T')

class PaginatedDataType(Generic[T]):
    items: list[T]
    total_count: int
    total_page: int
    current_page: int
    has_next: bool
    has_prev: bool
    

def get_paginated_queryset(queryset, page: int, size: int):
    """
    This function paginates a given queryset.

    Args:
        queryset (QuerySet): The queryset to be paginated.
        page (int): The page number to be returned.
        size (int): The number of items per page.

    Returns:
        QuerySet: A paginated queryset.
    """
    queryset = queryset.limit(size).offset((page - 1) * size)
    return queryset

def get_paginated_data(query, page_args, SchemaClass):
    """
    This function paginates and serializes a given query.

    Args:
        query (Query): The SQLAlchemy query to be paginated.
        page_args (dict): A dictionary containing 'page' and 'size' keys.
        SchemaClass (Schema): The Marshmallow schema of the items to be paginated.

    Returns:
        dict: A dictionary containing paginated and serialized data. 
        The dictionary includes fields for the items (using the provided SchemaClass), 
        total count of items, total pages, current page, and boolean fields 
        indicating if there are next or previous pages.
    """
    page = page_args.get('page') or 1
    size = page_args.get('size') or 10
    paginated_queryset = get_paginated_queryset(query, page, size)
    paginated_schema = get_paginated_schema(SchemaClass)()
    total_count = query.count()
    total_page = ceil(total_count / size)
    has_next = page < total_page
    has_prev = page > 1
    serialized_data = paginated_schema.dump({
        'items': paginated_queryset.all(),
        'total_count': total_count,
        'total_page': total_page,
        'current_page': page,
        'has_next': has_next,
        'has_prev': has_prev
    })
    return serialized_data

def get_page_args(args: dict): 
    """
    This function extracts pagination arguments from a dictionary.

    Args:
        args (dict): A dictionary from which to extract 'page' and 'size' keys.

    Returns:
        dict: A dictionary containing 'page' and 'size' keys.
    """
    page = args.pop('page') or 1
    size = args.pop('size') or 10
    return {'page': page, 'size': size}

def get_paginated_parser(parser: Optional[reqparse.RequestParser] = None, min_size: int = 3, max_size: int = 100):
    """
    This function adds pagination arguments to a Flask-RESTPlus request parser.

    Args:
        parser (Optional[reqparse.RequestParser]): The request parser to which to add arguments. 
            If None, a new request parser is created.
        min_size (int): The minimum allowed value for the 'size' argument. Default is 3.
        max_size (int): The maximum allowed value for the 'size' argument. Default is 100.

    Returns:
        reqparse.RequestParser: The request parser with added 'page' and 'size' arguments.
    """
    new_parser = reqparse.RequestParser()
    new_parser.add_argument('page', type=int, location='args', store_missing=False, help="The page number")
    new_parser.add_argument('size', type=inputs.int_range(min_size, max_size), store_missing=False, location='args', help="The number of items per page")
    if parser:
        for arg in parser.args:
            new_parser.add_argument(arg)

    return new_parser