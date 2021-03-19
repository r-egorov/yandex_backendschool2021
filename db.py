import sqlite3
import os

db_path = os.path.join("db", "database.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()


def _init_db():
    """Initializes the database"""
    with open(os.path.join("db", "create_db.sql"), "r", encoding="utf-8") as f:
        sql = f.read()
    cursor.execute(sql)
    conn.commit()


def check_db_exists():
    """
    Checks if db exists.
    If it does, connects to it.
    If it doesn't, connects to it and initialize it.
    """
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='couriers'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


def get_cursor():
    return cursor


def insert(table: str, column_values):
    """
    Inserts given values in the given table.
    The values have to given as a dictionary, where keys are the columns where
    the values have to be put.
    Parameters:
        table: str - the destination table name
        column_values: Dict - the column:value dictionary
    """
    columns = ", ".join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def update(table: str, row_id: int, column_values):
    """
    Updates given values of the given row in the given table.
    Parameters:
        table: str - the destination table name
        row_id: int - the ID of the row
        column_values: Dict - the column:value dictionary
    """
    columns = [key + " = ?" for key in column_values.keys()]
    columns_w_placeholders = ",\n".join(columns)
    values = [tuple(column_values.values())]
    cursor.executemany(
        f"UPDATE {table} "
        f"SET {columns_w_placeholders}"
        f"WHERE id = {row_id}",
        values)
    conn.commit()


def get_all(table: str, columns):
    """
    Fetches every row of the given columns from the given table.
    Parameters:
        table: str - the destination table name
        columns: List[str] - the columns that are needed to be fetched
    Returns:
        A list of column:value dictionaries
    """
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def get_id(table: str, row_id: int):
    """
    Fetches every row of the given columns from the given table.
    Parameters:
        table: str - the destination table name
        row_id: int - the columns that are needed to be fetched
    Returns:
        A list of column:value dictionaries
    """
    cursor.execute(f"SELECT * FROM {table} WHERE id={row_id}")
    row = cursor.fetchall()
    return row


def get_courier_ids():
    """
    Fetches every id of the existing courier.
    Returns:
        A list of ids
    """
    cursor.execute(f"SELECT id FROM couriers")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append(row[0])
    return result


def delete(table: str, row_id: int):
    row_id = int(row_id)
    cursor.execute(f"DELETE FROM {table} WHERE id={row_id}")
    conn.commit()


check_db_exists()