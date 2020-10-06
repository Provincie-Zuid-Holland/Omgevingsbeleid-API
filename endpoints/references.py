"""
Collection of reference objects including getting and setting behaviour
Link tablename should point to a view where the objects are joined.
"""
from globals import row_to_dict

class UUID_Reference:
    def __init__(self, target_tablename, link_tablename, self_column, target_column, schema):
        self.target_tablename = target_tablename
        self.link_tablename = link_tablename
        self.self_column = self_column
        self.target_column = target_column
        # Make an instance of the schema here
        self.schema = schema()


    def merge_references(self, rows, fieldname, cnx):
        """Gets all the references objects based on the UUID, requires a connection object."""
        cursor = cnx.cursor()
        query = f"SELECT * FROM {self.link_tablename}"
        linked_object = map(row_to_dict, cursor.execute(query))
        for row in rows:
            row[fieldname] = filter(lambda lo: lo.get(
                self.self_column) == row['UUID'], linked_object)
        return rows

    def store_references(self, self_uuid, targets, cnx):
        """Stores all the references objects based on the UUID, requires a connection object."""
        cursor = cnx.cursor()
        for target_uuid in targets:
            query = f'''INSERT INTO {self.link_tablename} ({self.self_column}, {self.target_column}) VALUES (?, ?)'''
            cursor.execute(query, self_uuid, target_uuid)

    def copy_references(self, old_uuid, self_uuid, cnx):
        """Copies reference from the old object"""
        cursor = cnx.cursor()
        query = f'''SELECT * FROM {self.link_tablename} WHERE {self.self_column} = ?'''
        targets = list(map(lambda t: t[self.target_column], map(
            row_to_dict, cursor.execute(query, old_uuid))))
        self.store_references(self_uuid, targets, cnx)

class ID_Reference:
    def __init__(self, target_tablename, link_tablename, self_column, target_column, version_column, schema):
        self.target_tablename = target_tablename
        self.link_tablename = link_tablename
        self.self_column = self_column
        self.target_column = target_column
        self.version_column = version_column
        # Make an instance of the schema here
        self.schema = schema()

    def merge_references(self, rows, fieldname, cnx):
        """Gets all the references objects based on the ID, requires a connection object."""
        cursor = cnx.cursor()
        query = f"SELECT * FROM {self.link_tablename}"
        linked_objects = list(map(row_to_dict, cursor.execute(query)))
        for row in rows:
            row[fieldname] = list(filter(lambda lo: lo.get(
                self.version_column) == row['UUID'], linked_objects))
        return rows

    def store_references(self, source, targets, cnx):
        """Stores all the references objects based on the ID, requires a connection object."""
        cursor = cnx.cursor()
        for target_id in targets:
            query = f'''INSERT INTO {self.link_tablename} ({self.self_column}, {self.target_column}, {self.version_column}) VALUES (?, ?, ?)'''
            cursor.execute(query, source['ID'], target_id, source['UUID'])

    def copy_references(self, old, new, cnx):
        """Gets all old relations and passes them to store_references, requires a connection object"""
        cursor = cnx.cursor()
        query = f'''SELECT * FROM {self.link_tablename} WHERE {self.version_column} = ?'''
        targets = list(map(lambda t: t[self.target_column], map(
            row_to_dict, cursor.execute(query, old['UUID']))))
        self.store_references(new, targets, cnx)