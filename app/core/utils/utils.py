def table_to_dict(object_table) -> dict:
    object_dict = dict(object_table.__dict__)
    object_dict.pop("_sa_instance_state", None)
    return object_dict


def bytes_to(bytes, to, bsize=1024):
    """
    Converts bytes to a different units

    Args:
        bytes (bytes): The bytes to convert
        to (string): Target unit descriptor ('k' for kb, 'm' for mb, 'g' for gb)
        bsize (int, optional): Defaults to 1024.

    Returns:
        [type]: [description]
    """
    a = {"k": 1, "m": 2, "g": 3}
    return float(bytes) / (bsize ** a[to])
