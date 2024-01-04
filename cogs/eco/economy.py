import sqlite3
from discord.ext import commands, tasks
import discord
import db
import random
import asyncio 
from datetime import datetime, timedelta



class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.all_shop_items = {
            '1': {'name': 'Enchanted Wand', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '2': {'name': 'Dark Crystal', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '3': {'name': 'Mystic Book', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '4': {'name': 'Shadow Cloak', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '5': {'name': 'Angelic Sword', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '6': {'name': 'Demon Bow', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '7': {'name': 'Sorcerer\'s Staff', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '8': {'name': 'Magic Amulet', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '9': {'name': 'Fallen Halo', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '10': {'name': 'Ethereal Armor', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '11': {'name': 'Spell Tome', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '12': {'name': 'Arcane Ring', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '13': {'name': 'Cursed Necklace', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '14': {'name': 'Phantom Boots', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '15': {'name': 'Celestial Shield', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '16': {'name': 'Mystic Orb', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '17': {'name': 'Spirit Dagger', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '18': {'name': 'Witch\'s Cauldron', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '19': {'name': 'Angel\'s Feather', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'},
            '20': {'name': 'Dark Potion', 'image_url': 'https://github.com/ebagcoder/aimeebot/blob/main/image/items/notexture.png'}
        }

        self.shop_items = {}



    @commands.command(aliases=['w', 'job'])
    async def work(self, ctx):
        user_id = ctx.author.id
        earnings = random.randint(10, 100)  # Random earnings between 10 and 100

        # Ensure the user exists in the database and create if not
        if db.get_user_data(user_id) is None:
            db.add_new_user(user_id)
        
        # Update the balance of the user in the database
        db.update_balance(user_id, earnings)
        new_balance = db.get_balance(user_id)  # Get updated balance

        # Create an embed to display the work earnings
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Work Earnings",
            color=discord.Colour.random()
        )
        embed.add_field(name="Earnings", value=f"{earnings} souls", inline=False)
        embed.add_field(name="New Balance", value=f"{new_balance} souls", inline=False)
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")

        await ctx.send(embed=embed)

    @commands.command(aliases=['pay', 'sendsouls'])
    async def give(self, ctx, member: discord.Member, amount: int):
        sender_id = ctx.author.id
        recipient_id = member.id
        
        # Check if sender has enough balance
        if db.get_balance(sender_id) >= amount:
            db.update_balance(sender_id, -amount)
            db.update_balance(recipient_id, amount)
            db.log_transaction(sender_id, -amount, 'give')
            db.log_transaction(recipient_id, amount, 'receive')
            await ctx.send(f"You gave {member.display_name} {amount} souls.")
        else:
            await ctx.send("You don't have enough souls.")

    @commands.command(aliases=['bal', 'money'])
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        balance = db.get_balance(member.id)
        
        embed = discord.Embed(
            title=f"{member.display_name}'s Balance",
            color=discord.Colour.random()
        )
        embed.add_field(name="Balance", value=f"{balance} souls", inline=False)
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
        
        await ctx.send(embed=embed)

    @commands.command(aliases=['baltop', 'moneytop'])
    async def bal_leaderboard(self, ctx):
        top_users = db.get_top_users_by_balance()  # This function needs to be implemented in db.py
        leaderboard_description = "\n".join(
            f"{idx + 1}. <@{user_id}> - {balance} souls"
            for idx, (user_id, balance) in enumerate(top_users)
        )
        
        embed = discord.Embed(
            title="Balance Leaderboard",
            description=leaderboard_description,
            color=discord.Colour.random()
        )
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")

    @commands.command(aliases=['inv'])
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        inventory_items = db.get_user_inventory(member.id)  # Fetch inventory items from database

        # Check if inventory_items is not empty
        if not inventory_items:
            await ctx.send(f"{member.display_name} has no items in their inventory.")
            return

        for item in inventory_items:
            embed = discord.Embed(title=f"{member.display_name}'s Inventory", description=f"{item['name']}\nQuantity: {item['quantity']}", color=discord.Colour.random())
            # Assuming each item in inventory_items has 'image_url' key
            embed.set_image(url=item['image_url'])
            embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
            await ctx.send(embed=embed)


    @commands.command(aliases=['store'])
    async def shop(self, ctx):
        # Select 4 random items and assign random prices
        selected_items = random.sample(list(self.all_shop_items.values()), 4)

        for item in selected_items:
            price = random.randint(50, 500)
            # Create an embed for each item
            embed = discord.Embed(title=f"{item['name']}", description=f"Price: {price} souls", color=discord.Colour.random())
            # Set the thumbnail to the item's image
            embed.set_thumbnail(url=item['image_url'].replace('/blob/', '/raw/'))  # Ensure this is the raw image URL

            embed.set_footer(text="Type the name of the item to purchase it.")
            # Send the embed for the current item
            await ctx.send(embed=embed)

        # Check that it's the same user and in the same channel
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in (item['name'].lower() for item in self.shop_items.values())

        try:
            response = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.display_name}, you took too long to respond!")
            return

        # Find the item by name
        item_name = response.content.lower()
        item = next((item for key, item in self.shop_items.items() if item['name'].lower() == item_name), None)

        if item:
            user_id = ctx.author.id
            balance = db.get_balance(user_id)

            if balance >= item['price']:
                db.update_balance(user_id, -item['price'])
                db.add_item_to_inventory(user_id, item['name'])
                await ctx.send(f"You have purchased {item['name']} for {item['price']} souls.")
            else:
                await ctx.send("You do not have enough souls to purchase this item.")
        else:
            await ctx.send("Item not found in the shop.")           

def setup(bot):
    bot.add_cog(Economy(bot))
