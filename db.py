import mysql.connector
from mysql.connector import errorcode
import os
import json

# Charger la configuration de la base de données
with open(os.path.join('conf', 'config.json')) as config_file:
    config = json.load(config_file)

db_config = {
    'user': config['database']['username'],
    'password': config['database']['password'],
    'host': config['database']['host'],
    'database': config['database']['name'],
    'raise_on_warnings': True
}

# Fonction pour obtenir la connexion à la base de données
def get_db_connection():
    try:
        cnx = mysql.connector.connect(**db_config)
        return cnx
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Erreur d'authentification : Utilisateur ou mot de passe incorrect.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Erreur : Base de données n'existe pas.")
        else:
            print(err)
        return None

def create_line(table, data):
    """
    Insert a new line into the specified table.

    Args:
        table (str): The name of the table.
        data (dict): A dictionary containing column names as keys and corresponding values to insert.

    Returns:
        None
    """
    cnx = get_db_connection()
    if cnx is None:
        return

    placeholders = ", ".join(["%s"] * len(data))
    columns = ", ".join(data.keys())
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    try:
        cursor = cnx.cursor()
        cursor.execute(query, list(data.values()))
        cnx.commit()
        print("Record inserted successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        cnx.close()

def read_lines(table, conditions=None):
    """
    Retrieve lines from the specified table.

    Args:
        table (str): The name of the table.
        conditions (dict, optional): A dictionary containing column names as keys and values to filter records.

    Returns:
        list: A list of dictionaries representing the retrieved records.
    """
    cnx = get_db_connection()
    if cnx is None:
        return []

    query = f"SELECT * FROM {table}"
    if conditions:
        query += " WHERE " + " AND ".join(f"{k}=%s" for k in conditions.keys())
    
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(query, list(conditions.values()) if conditions else None)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    finally:
        cursor.close()
        cnx.close()

def update_line(table, data, conditions):
    """
    Update an existing line in the specified table.

    Args:
        table (str): The name of the table.
        data (dict): A dictionary containing column names as keys and corresponding values to update.
        conditions (dict): A dictionary containing column names as keys and values to identify the record to update.

    Returns:
        None
    """
    cnx = get_db_connection()
    if cnx is None:
        return

    set_clause = ", ".join(f"{k}=%s" for k in data.keys())
    where_clause = " AND ".join(f"{k}=%s" for k in conditions.keys())
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    
    try:
        cursor = cnx.cursor()
        cursor.execute(query, list(data.values()) + list(conditions.values()))
        cnx.commit()
        print("Record updated successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        cnx.close()

def delete_line(table, conditions):
    """
    Delete a line from the specified table.

    Args:
        table (str): The name of the table.
        conditions (dict): A dictionary containing column names as keys and values to identify the record to delete.

    Returns:
        None
    """
    cnx = get_db_connection()
    if cnx is None:
        return

    where_clause = " AND ".join(f"{k}=%s" for k in conditions.keys())
    query = f"DELETE FROM {table} WHERE {where_clause}"
    
    try:
        cursor = cnx.cursor()
        cursor.execute(query, list(conditions.values()))
        cnx.commit()
        print("Record deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        cnx.close()

def line_exists(table, conditions):
    """
    Check if a line exists in the specified table.

    Args:
        table (str): The name of the table.
        conditions (dict): A dictionary containing column names as keys and values to identify the record.

    Returns:
        bool: True if the record exists, False otherwise.
    """
    cnx = get_db_connection()
    if cnx is None:
        return False

    where_clause = " AND ".join(f"{k}=%s" for k in conditions.keys())
    query = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"

    try:
        cursor = cnx.cursor()
        cursor.execute(query, list(conditions.values()))
        result = cursor.fetchone()
        return result is not None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        cursor.close()
        cnx.close()


# Exemple d'utilisation
# create_line("artiste", {"id": 2, "name": "Daft Punk", "popularity": "100", "photo": "https://i.scdn.co/image/ab67616d0000b273f4c3b4e4b4e4b4e4b4e4b4e4"})