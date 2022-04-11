def row_to_dict(row):
    """
    Turns a row from pyodbc into a dictionary
    """
    return dict(zip([t[0] for t in row.cursor_description], row))
