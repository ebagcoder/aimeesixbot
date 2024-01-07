import sqlite3
from config import DATABASE_PATH
import json 

def get_db_connection():
    """
    Create and return a database connection.
    """
    return sqlite3.connect(DATABASE_PATH)

def initialize_db():
    """
    Initialize the database with the required tables and columns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create or modify the user_data table to include a balance column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        xp INTEGER NOT NULL DEFAULT 0,
        level INTEGER NOT NULL DEFAULT 0,
        last_message_timestamp INTEGER,
        balance INTEGER NOT NULL DEFAULT 0
    )
    '''),
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (user_id, item_name),
        FOREIGN KEY (user_id) REFERENCES user_data(user_id) -- Link to your user_data table
    )
    ''')

    # Check if the balance column exists, if not, add it
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [info[1] for info in cursor.fetchall()]
    if "balance" not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN balance INTEGER NOT NULL DEFAULT 0")

    # Add a column for last_daily_claim to user_data if it doesn't exist
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [info[1] for info in cursor.fetchall()]
    if "last_daily_claim" not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN last_daily_claim INTEGER")

    conn.commit()
    conn.close()




def add_new_user(user_id):
    """
    Add a new user to the database with default values.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_data (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def update_user_xp(user_id, xp, timestamp):
    """
    Update a user's XP and last message timestamp.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_data SET xp = ?, last_message_timestamp = ? WHERE user_id = ?", (xp, timestamp, user_id))
    conn.commit()
    conn.close()

def update_user_level(user_id, level):
    """
    Update a user's level.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_data SET level = ? WHERE user_id = ?", (level, user_id))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    """
    Get the top users based on XP.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, xp, level FROM user_data ORDER BY xp DESC LIMIT ?", (limit,))
    top_users = cursor.fetchall()
    conn.close()
    return top_users

# Economy system functions

def get_balance(user_id):
    """
    Get the balance of a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM user_data WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()
    conn.close()
    return balance[0] if balance else 0

def update_balance(user_id, amount):
    """
    Update a user's balance. Add user if they do not exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM user_data WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        # If the user doesn't exist, insert them with the new balance
        cursor.execute("INSERT INTO user_data (user_id, balance) VALUES (?, ?)", (user_id, amount))
    else:
        # If the user exists, update their balance
        cursor.execute("UPDATE user_data SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def log_transaction(user_id, amount, transaction_type):
    """
    Log a transaction in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id, amount, transaction_type) VALUES (?, ?, ?)", (user_id, amount, transaction_type))
    conn.commit()
    conn.close()

def get_top_users_by_balance(limit=10):
    """
    Get the top users based on balance.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM user_data ORDER BY balance DESC LIMIT ?", (limit,))
    top_users = cursor.fetchall()
    conn.close()
    return top_users


def get_user_data(user_id):
    """
    Retrieve user data from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def update_last_daily_claim(user_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_data SET last_daily_claim = ? WHERE user_id = ?", (timestamp, user_id))
    conn.commit()
    conn.close()

def add_item_to_inventory(user_id, item_name):
    conn = get_db_connection()  # Assuming you have a function to get your database connection
    cursor = conn.cursor()

    # Check if the item already exists in the user's inventory
    cursor.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, item_name))
    result = cursor.fetchone()

    if result:
        # Update the quantity of the existing item
        new_quantity = result[0] + 1
        cursor.execute("UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_name = ?", (new_quantity, user_id, item_name))
    else:
        # Add a new item to the inventory with quantity 1
        cursor.execute("INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, ?)", (user_id, item_name, 1))

    conn.commit()
    conn.close()

def get_user_inventory(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all items from the user's inventory
    cursor.execute("SELECT item_name, quantity FROM inventory WHERE user_id = ?", (user_id,))
    inventory_items = [{'name': row[0], 'quantity': row[1]} for row in cursor.fetchall()]

    conn.close()
    return inventory_items


def get_server_config(guild_id):
    """
    Retrieve server configuration for a specific guild.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM server_config WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        guild_id, allowed_roles, birthday_channel_id, level_up_channel_id = row
        return {
            'guild_id': guild_id,
            'allowed_roles': json.loads(allowed_roles) if allowed_roles else [],
            'birthday_channel_id': birthday_channel_id,
            'level_up_channel_id': level_up_channel_id
        }
    return None

def set_server_config(guild_id, allowed_roles, birthday_channel_id, level_up_channel_id):
    """
    Set server configuration for a specific guild.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    allowed_roles_json = json.dumps(allowed_roles)  # Encode the list of roles as JSON
    cursor.execute("""
        INSERT INTO server_config (guild_id, allowed_roles, birthday_channel_id, level_up_channel_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id)
        DO UPDATE SET 
            allowed_roles = excluded.allowed_roles,
            birthday_channel_id = excluded.birthday_channel_id,
            level_up_channel_id = excluded.level_up_channel_id
        """, (guild_id, allowed_roles_json, birthday_channel_id, level_up_channel_id))
    conn.commit()
    conn.close()



if __name__ == "__main__":
    initialize_db()
    print("Database initialized.")