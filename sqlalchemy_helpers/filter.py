from typing import TypedDict, Literal, Any, Callable, Union, cast
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import or_

FilterType = Literal['eq', 'ne', 'lt', 'le', 'gt', 'ge', 'like', 'ilike', 'ends', 'starts', 'in', 'not_in', 'is_null', 'is_not_null']

def get_filter_arg(field: Any, value: Any, filter_type: FilterType):
    """
    This function generates a SQLAlchemy filter argument based on the provided field, value, and filter type.

    Args:
        field (Any): The field to be filtered.
        value (Any): The value to be used in the filter.
        filter_type (FilterType): The type of filter to be applied. 
            This can be one of the following: 'eq', 'ne', 'lt', 'le', 'gt', 'ge', 'like', 'ilike', 
            'starts', 'ends', 'istarts', 'iends', 'in', 'not_in', 'contains', 'is_null', 'is_not_null'.

    Returns:
        BinaryExpression: A SQLAlchemy BinaryExpression representing the filter.

    Raises:
        ValueError: If an invalid filter type is provided.
    """
    if filter_type == 'eq':
        return field == value
    elif filter_type == 'ne':
        return field != value
    elif filter_type == 'lt':
        return field < value
    elif filter_type == 'le':
        return field <= value
    elif filter_type == 'gt':
        return field > value
    elif filter_type == 'ge':
        return field >= value
    elif filter_type == 'like':
        return field.like(f'%{value}%')
    elif filter_type == 'ilike':
        return field.ilike(f'%{value}%')
    elif filter_type == 'starts':
        return field.startswith(value)
    elif filter_type == 'ends':
        return field.endswith(value)
    elif filter_type == 'istarts':
        return field.ilike(f"{value}%")
    elif filter_type == 'iends':
        return field.ilike(f"%{value}")
    elif filter_type == 'in':
        return field.in_(value)
    elif filter_type == 'not_in':
        return field.notin_(value)
    elif filter_type == 'contains':
        return field.contains(value)
    elif filter_type == 'is_null':
        return field.is_(None)
    elif filter_type == 'is_not_null':
        return field.isnot(None)
    else:
        raise ValueError(f"Invalid filter type: {filter_type}")

class FieldConfigValueTypeBase(TypedDict):
    field: InstrumentedAttribute[Any]

class FieldConfigValueType(FieldConfigValueTypeBase, total=False):
    look_up: FilterType
    wrapper: Callable
    

FilterConfigDictType = FieldConfigValueType
FilterConfigListType = list[FieldConfigValueType]
FilterConfigType = dict[str, Union[FilterConfigDictType, FilterConfigListType]]

def get_filtered_query(model, args, field_config: FilterConfigType = {}, join_models=[], ignore_deleted=False):
    """
    This function generates a filtered SQLAlchemy query based on the provided model, arguments, and field configuration.

    Args:
        model (Model): The SQLAlchemy model to be queried.
        args (dict): A dictionary containing the filter arguments.
        field_config (FilterConfigType): A dictionary or list containing the field configuration for the filter. 
            If a dictionary is provided, it should map keys to another dictionary with 'field', 'look_up', and 'wrapper' keys. 
            If a list is provided, it should contain dictionaries with 'field', 'look_up', and 'wrapper' keys.

    Returns:
        Query: A SQLAlchemy query filtered according to the provided arguments and field configuration.
    """
    filter_arguments = []
    for key, value in field_config.items():
        if type(value) == dict:
            value = cast(FieldConfigValueType, value)
            field, filter_type, data_value, wrapper = value['field'], value.get('look_up', 'eq'), args.get(key), value.get('wrapper')
            if not data_value: continue
            filter_arg = get_filter_arg(field, args[key], filter_type)
            # wrapper is for the query expressions like Patient.query.filter(Patient.tags.any(Tag.id.in_(filter_tag_ids))).all()
            # the wrapper will be Patient.tags.any, field will be Tag.id.in_ and data[key] will be filter_tag_ids
            filter_args = wrapper(filter_arg) if wrapper else filter_arg
            filter_arguments.append(filter_args)
        # if the value is a list, then we will use the or_ function to combine the filter arguments
        elif type(value) == list:
            or_filter_arguments = []
            for filter_config in value:
                field, filter_type, data_value, wrapper = filter_config['field'], filter_config.get('look_up', 'eq'), args.get(key), filter_config.get('wrapper')
                if not data_value: continue
                filter_arg = get_filter_arg(field, args[key], filter_type)
                filter_arg = wrapper(filter_arg) if wrapper else filter_arg
                or_filter_arguments.append(filter_arg)
            filter_arguments.append(or_(*or_filter_arguments))

    query = model.query
    for join_model in join_models:
        query = query.join(join_model)
        
    if ignore_deleted:
        filter_arguments.append(model.deleted == False)
    
    return query.filter(*filter_arguments).distinct(model.id)

