import sqlite3
import os

db_path = os.path.join("db", "database.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()


def _init_db():
    """Initializes the database"""
    with open(os.path.join("db", "create_db.sql"), "r", encoding="utf-8") as f:
        sql = f.read()
    cursor.executescript(sql)
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


def insert_one(table: str, column_values):
    """
    Inserts given values in the given table.
    The values have to be given as a dictionary, where keys are the columns where
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


def insert_many(table: str, column_values):
    """
    Inserts a list of given values in the given table.
    The values have to be given as a list of tuples, where list[0] is
    a tuple of columns where values have to be put.
    Parameters:
        table: str - the destination table name
        column_values: List - the list element[0] of which is a tuple of
        columns, other elements are values which are to put
    """
    columns = ", ".join(column_values[0])
    values = [value for value in column_values[1:]]
    placeholders = ", ".join("?" * len(column_values[0]))
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
    Fetches a row of the given columns from the given table with the id.
    Parameters:
        table: str - the destination table name
        row_id: int - the columns that are needed to be fetched
    Returns:
        A tuple of row values
    """
    cursor.execute(f"SELECT * FROM {table} WHERE id={row_id}")
    row = cursor.fetchone()
    return row


def get_ids(table: str):
    """
    Fetches every id of the existing courier.
    Returns:
        A list of ids
    """
    cursor.execute(f"SELECT id FROM {table}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append(row[0])
    return result


def get_free_orders():
    """
    Fetches every row from the table 'orders' which was not assigned.
    Returns:
        A list of column:value dictionaries
    """
    columns = ["id", "weight", "region", "delivery_hours", "assigned", "completed"]
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM orders "
                   f"WHERE assigned = 0")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def get_assigned_orders(courier_id, complete=False, incomplete=False):
    """
    Fetches every row from the table 'orders' which is associated
    with the given courier in the table 'orders_assigned'.
    Returns:
        A list of column:value dictionaries
    """
    columns = ["id", "weight", "region", "delivery_hours", "assigned", "completed"]
    completed_flag = 0
    if complete or incomplete:
        columns.append("assign_time")
        columns.append("complete_time")
        if complete:
            completed_flag = 1
    columns_joined = ", ".join(columns)
    sql = f"SELECT {columns_joined} FROM orders o " \
          f"JOIN orders_assigned oa ON o.id = oa.order_id " \
          f"WHERE oa.courier_id = {courier_id}"
    if complete or incomplete:
        sql += f" AND o.completed = {completed_flag}"
    cursor.execute(sql)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def assign_orders(courier_id: int, orders: list, timestamp):
    """
    Assigns given list of orders to the given courier
    Params:
        courier_id: int - id of the courier
        orders: list - a list of orders to assign
        timestamp: string - formatted string of the timestamp
    """
    if not orders:
        return
    insert_values = []
    order_ids = []
    for order in orders:
        insert_values.append("({}, {}, \'{}\')".format(
            order.id, courier_id, timestamp
        ))
        order_ids.append(str(order.id))
    order_ids_joined = '(' + ",".join(order_ids) + ')'
    insert_sql = "INSERT INTO orders_assigned " \
                 "(order_id, courier_id, assign_time) " \
                 "VALUES " + ", ".join(insert_values)
    update_sql = "UPDATE orders SET assigned = 1 " \
                 "WHERE [id] in {}".format(order_ids_joined)
    cursor.executescript(insert_sql + "; " + update_sql + ';')


def dismiss_orders(orders: list):
    """
    Dismisses given list of orders from the orders_assigned table
    Params:
        orders: list - a list of orders to dismiss
    """
    if not orders:
        return
    order_ids = [str(order.id) for order in orders]
    order_ids_joined = '(' + ",".join(order_ids) + ')'
    delete_sql = "DELETE FROM orders_assigned " \
                 "WHERE [order_id] in {}".format(order_ids_joined)
    update_sql = "UPDATE orders SET assigned = 0 " \
                 "WHERE [id] in {}".format(order_ids_joined)
    cursor.executescript(delete_sql + "; " + update_sql + ';')


def delete(table: str, row_id: int):
    row_id = int(row_id)
    cursor.execute(f"DELETE FROM {table} WHERE id={row_id}")
    conn.commit()


check_db_exists()
