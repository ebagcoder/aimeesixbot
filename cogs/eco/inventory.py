import sqlite3
from discord.ext import commands, tasks
import discord
import random
import asyncio
import requests
import db
from discord.ext.commands import has_permissions, CheckFailure

def has_allowed_role():
    async def predicate(ctx):
        # Check if the user has any of the allowed roles
        user_roles = [role.name for role in ctx.author.roles]
        if any(role in user_roles for role in ALLOWED_ROLES):
            return True
        else:
            raise CheckFailure("You don't have the required role to use this command.")
    return commands.check(predicate)

DATABASE_PATH = 'economy.db'

def get_user_inventory(user_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Retrieve inventory items for the user
    cursor.execute('SELECT item_name, quantity FROM inventory WHERE user_id = ?', (user_id,))
    inventory = [{'name': row[0], 'quantity': row[1]} for row in cursor.fetchall()]
    
    conn.close()
    return inventory

def initialize_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create tables if they do not exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER,
        item_name TEXT,
        quantity INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )''')

    conn.commit()
    conn.close()

# Call this function somewhere in your bot setup code
initialize_database()

class inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def create_inventory_text(self, user_id):
        inventory_items = db.get_user_inventory(user_id)  # Fetch inventory items from the database

        inventory_text = "Inventory:\n"
        for item in inventory_items:
            item_name = item['name']
            quantity = item['quantity']
            inventory_text += f"{item_name}: {quantity}\n"

        return inventory_text

    # Replace the existing 'inventory' command with this updated version
    @commands.command(aliases=['inv'])
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        # Actual data retrieval
        inventory_text = await self.create_inventory_text(member.id)  # Pass the member's ID to get their inventory

        embed = discord.Embed(title=f"{member.display_name}'s Inventory", description=inventory_text, color=discord.Colour.random())
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")

        await ctx.send(embed=embed)
def setup(bot):
    bot.add_cog(inventory(bot))