import discord
from discord.ext import commands
import os
import sqlite3
import db
from db import initialize_db
import logging
from discord.ext.commands import CheckFailure
from config import ALLOWED_ROLES

logging.basicConfig(level=logging.INFO)

db.initialize_db()

bot = commands.Bot(command_prefix='!', case_insensitive=True)

import config

# Database setup
def setup_database():
    conn = sqlite3.connect('birthdays.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS birthdays 
                 (member_id INTEGER PRIMARY KEY, date TEXT)''')
    conn.commit()
    conn.close()

# Load cogs on startup
for root, dirs, files in os.walk('./cogs'):
    for filename in files:
        if filename.endswith('.py') and filename != "__init__.py":
            # Construct the cog module path
            rel_path = os.path.relpath(root, '.')  # Relative path of the root
            module_name = os.path.join(rel_path, filename).replace(os.sep, '.').replace('/', '.').replace('\\', '.')
            extension = module_name[:-3]  # Remove '.py' from the end
            bot.load_extension(extension)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="AimeeSixx")
    await bot.change_presence(activity=activity)
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    setup_database()

initialize_db()
print("Database initialized.")

def has_allowed_role():
    async def predicate(ctx):
        if not ctx.guild:  # Check if command is run in a server
            raise CheckFailure("This command can only be used in a server.")
        # Check if any of the allowed roles is in the user's roles
        if any(role.id in ALLOWED_ROLES for role in ctx.author.roles):
            return True
        # If the user does not have the role, raise a CheckFailure
        raise CheckFailure("You do not have the required role to use this command.")
    return commands.check(predicate)



bot.run(config.TOKEN)
