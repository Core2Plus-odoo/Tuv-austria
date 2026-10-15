def search_values(value):
    """The values of a domain leaf handed to a field's search method, as a list.

    Odoo 19 normalises ('field', '=', True) to ('field', 'in', <OrderedSet {True}>)
    before it reaches the search method, but a plain value or list can still arrive.
    """
    if isinstance(value, (str, bytes)) or not hasattr(value, '__iter__'):
        return [value]
    return list(value)


def boolean_search_positive(operator, value):
    """True when a boolean filter asks for the records where the field is set."""
    positive = any(search_values(value))
    if operator in ('!=', 'not in'):
        positive = not positive
    return positive
