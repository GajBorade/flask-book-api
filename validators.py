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
        return False, invalid_keys  # validation failed
    return True, None  # all good


# Validate Page
def page_validation(page, total_books, limit):
    """
    Validates the 'page' query parameter.

    :param page: str or int from request.args
    :param limit: int (books per page, say 10 per page)
    :param total_books: int (total number of books in json)
    :return: int (valid page number) or raises ValueError
    """
    if not page:
        return 1

    try:
        page = int(page)
    except ValueError:
        raise ValueError("Page must be an integer")

    if page < 1:
        raise ValueError("Page must be >=1 ")

    max_page = total_books // limit
    if total_books % limit != 0:
        max_page += 1

    if page > max_page:
        raise ValueError(f"Page must not be > {max_page= }")

    return page


# Validate limit
def limit_validation(limit, max_limit=None):
    """
    Validates the 'limit' query parameter

    :param limit: str or int from request.args
    :param max_limit: optional maximum allowed limit
    :return: int (validated limit) or raise ValueError
    """
    if max_limit is None:
        max_limit = 10  # Default maximum limit

    try:
        limit = int(limit)
    except ValueError:
        raise ValueError("limit must be an integer")

    if limit < 1:
        raise ValueError("limit must be >= 1")

    if limit > max_limit:
        raise ValueError(f"limit must not exceed {max_limit= }")

    return limit
