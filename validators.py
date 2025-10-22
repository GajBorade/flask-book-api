# Validate ID Conversion
def validate_book_id(book_id):
    try:
        return int(book_id)
    except ValueError:
        return None

# Validate data
def validate_book_data(data):
    if "title" not in data or "author" not in data:
        return False
    return True

def validate_query_parameters(query_parameters, valid_keys):
    """
    Validate query parameters sent by the user.

    Checks whether all provided keys in the query string are valid.

    :param query_parameters: dict of query parameters entered by
                                the client in the URL (after ?)

    :param valid_keys: set or list of valid query keys that the client
                        is allowed to use

    :returns: tuple
         - (True, None) if all query keys are valid
        - (False, invalid_keys) if one or more query keys are invalid,
        where invalid_keys is a list of the invalid keys
    """
    invalid_keys = []

    for key in query_parameters:
        if key not in valid_keys:
            invalid_keys.append(key)

    if invalid_keys:
        return False, invalid_keys # validation failed
    return True, None              # all good