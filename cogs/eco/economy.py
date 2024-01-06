import sqlite3
from discord.ext import commands, tasks
import discord
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

SOUL_AWARD_CHANCE = 0.05  # 10% chance to get souls on each message
MIN_SOULS = 10
MAX_SOULS = 150


JOBS = {
    'Hunting': {
        'earnings': (15, 150),
        'items': ['Fur', 'Bone', 'Leather'],
        'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'
    },
    'Mining': {
        'earnings': (20, 200),
        'items': ['Coal', 'Iron', 'Gold'],
        'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'
    },
    'Farming': {
        'earnings': (10, 120),
        'items': ['Wheat', 'Corn', 'Vegetables'],
        'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'
    }
}

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.all_shop_items = {
            '1': {'name': 'Enchanted Wand', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '2': {'name': 'Dark Crystal', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '3': {'name': 'Mystic Book', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '4': {'name': 'Shadow Cloak', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '5': {'name': 'Angelic Sword', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '6': {'name': 'Demon Bow', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '7': {'name': 'Sorcerer\'s Staff', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '8': {'name': 'Magic Amulet', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '9': {'name': 'Fallen Halo', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '10': {'name': 'Ethereal Armor', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '11': {'name': 'Spell Tome', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '12': {'name': 'Arcane Ring', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '13': {'name': 'Cursed Necklace', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '14': {'name': 'Phantom Boots', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '15': {'name': 'Celestial Shield', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '16': {'name': 'Mystic Orb', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '17': {'name': 'Spirit Dagger', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '18': {'name': 'Witch\'s Cauldron', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '19': {'name': 'Angel\'s Feather', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'},
            '20': {'name': 'Dark Potion', 'image_url': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png'}
        }

    


        self.shop_items = {}

        self.item_image_urls = {
            'fur': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/fur.png',
            'coal': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/coal.png',
            'wheat': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/wheat.png',
            'bone': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/bone.png',
            'leather': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/leather.png',
            'iron': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/iron.png',
            'gold': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/gold.png',
            'corn': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/corn.png',
            'vegetables': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/vegetables.png',
            'Unknown Item': 'https://github.com/ebagcoder/aimeesixbot/blob/main/image/items/texturenotfound.png',
        }

    # Function to fetch an image from a URL
    def fetch_image(url):
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        return Image.open(BytesIO(response.content))

    # Function to overlay item images and quantities onto the base inventory image
    async def create_inventory_image(self, inventory_items):
        # URL of the base inventory image
        base_image_url = "https://raw.githubusercontent.com/ebagcoder/aimeesixbot/main/image/gui/inventory.png"
        
        # Retrieve the base inventory image from the URL
        response = requests.get(base_image_url)
        base_image = Image.open(BytesIO(response.content))

        # Define positions for the first slot (you'll need to adjust these)
        slot_positions = [(x, y) for y in range(0, 300, 50) for x in range(0, 300, 50)]

        for index, item in enumerate(inventory_items):
            if index < len(slot_positions):
                item_name = item['name'].lower()  # Ensure item names are in lower case to match keys
                item_quantity = item['quantity']
                item_image_url = self.item_image_urls.get(item_name)

                if item_image_url:
                    # Fetch and resize the item image
                    item_image = Image.open(BytesIO(requests.get(item_image_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')).content))
                    item_image.thumbnail((50, 50), Image.ANTIALIAS)  # Resize the item image to fit the slot

                    # Position the item image onto the base inventory image
                    base_image.paste(item_image, slot_positions[index], item_image)

                    # Draw the quantity number
                    draw = ImageDraw.Draw(base_image)
                    font_size = 14  # Font size for quantity numbers
                    font = ImageFont.truetype("arial.ttf", font_size)  # Load a truetype font
                    text_pos = (slot_positions[index][0] + 35, slot_positions[index][1] + 35)  # Position for quantity text
                    draw.text(text_pos, str(item_quantity), font=font, fill='white')

        # Save the edited image to a bytes buffer
        final_buffer = BytesIO()
        base_image.save(final_buffer, 'PNG')
        final_buffer.seek(0)

        return final_buffer

    # URL for the base inventory image and a dictionary mapping item names to their image URLs
    base_inventory_url = "https://raw.githubusercontent.com/ebagcoder/aimeesixbot/main/image/gui/inventory.png"
    item_images = {
        'ItemName1': 'https://example.com/path/to/item1.png',  # Replace with actual item image URLs
        'ItemName2': 'https://example.com/path/to/item2.png',
        # Add more items as needed
    }

    # Sample inventory data, replace with actual inventory data retrieval logic
    inventory_items = {
        'ItemName1': 42,
        'ItemName2': 16,
        # Add more items as needed
    }

    # Create the inventory image
    inventory_image_bytes = create_inventory_image(base_inventory_url, inventory_items, item_images)

    # Show the image (for testing purposes)
    # In actual bot usage, you would send this image in a Discord message instead
    Image.open(inventory_image_bytes).show()




    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore bot messages

        # Randomly award souls with a given chance
        if random.random() < SOUL_AWARD_CHANCE:
            # Calculate random amount of souls to award
            souls_to_award = random.randint(MIN_SOULS, MAX_SOULS)
            
            # Update the user's balance in the database
            db.update_balance(message.author.id, souls_to_award)
            
            # Send a message to the channel notifying the user
            await message.channel.send(f"{message.author.mention} You found {souls_to_award} souls while chatting!")



    @commands.command(aliases=['job'])
    async def work(self, ctx):
        user_id = ctx.author.id
        job_type = random.choice(list(JOBS.keys()))
        job_info = JOBS[job_type]

        # Random earnings and item based on job type
        earnings = random.randint(*job_info['earnings'])
        item_gained = random.choice(job_info['items'])
        
        # Convert GitHub URL to raw content URL
        raw_image_url = job_info['image_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        # Ensure the user exists in the database and create if not
        if db.get_user_data(user_id) is None:
            db.add_new_user(user_id)
        
        # Update the balance of the user in the database
        db.update_balance(user_id, earnings)
        # Add the item to the user's inventory in the database
        db.add_item_to_inventory(user_id, item_gained)
        
        new_balance = db.get_balance(user_id)  # Get updated balance
        
        # Create an embed to display the work earnings and item gained
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s {job_type} Results",
            description=f"While {job_type.lower()}ing, you earned some souls and found an item!",
            color=discord.Colour.random()
        )
        embed.set_thumbnail(url=raw_image_url)
        embed.add_field(name="Earnings", value=f"{earnings} souls", inline=False)
        embed.add_field(name="Item Gained", value=item_gained, inline=False)
        embed.add_field(name="New Balance", value=f"{new_balance} souls", inline=False)
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
        
        await ctx.send(embed=embed)

    @commands.command()
    async def job_hunt(self, ctx):
        await self.perform_job(ctx, 'Hunting')

    @commands.command()
    async def job_mine(self, ctx):
        await self.perform_job(ctx, 'Mining')

    @commands.command()
    async def job_farm(self, ctx):
        await self.perform_job(ctx, 'Farming')

    async def perform_job(self, ctx, job_type):
        user_id = ctx.author.id
        job_info = JOBS[job_type]

        # Random earnings and item based on job type
        earnings = random.randint(*job_info['earnings'])
        item_gained = random.choice(job_info['items'])
        
        # Convert GitHub URL to raw content URL
        raw_image_url = job_info['image_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        # Ensure the user exists in the database and create if not
        if db.get_user_data(user_id) is None:
            db.add_new_user(user_id)
        
        # Update the balance of the user in the database
        db.update_balance(user_id, earnings)
        # Add the item to the user's inventory in the database
        db.add_item_to_inventory(user_id, item_gained)
        
        new_balance = db.get_balance(user_id)  # Get updated balance
        
        # Create an embed to display the work earnings and item gained
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s {job_type} Results",
            description=f"While {job_type.lower()}ing, you earned some souls and found an item!",
            color=discord.Colour.random()
        )
        embed.set_thumbnail(url=raw_image_url)
        embed.add_field(name="Earnings", value=f"{earnings} souls", inline=False)
        embed.add_field(name="Item Gained", value=item_gained, inline=False)
        embed.add_field(name="New Balance", value=f"{new_balance} souls", inline=False)
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
        
        await ctx.send(embed=embed)

    @commands.command(aliases=['inv'])
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        inventory_items = db.get_user_inventory(member.id)  # Fetch inventory items from the database

        # Check if the inventory is empty
        if not inventory_items:
            await ctx.send(f"{member.display_name} has no items in their inventory.")
            return

        for item in inventory_items:
            item_name = item.get('name', 'Unknown Item')  # Safely get the item name
            item_quantity = item.get('quantity', 0)      # Safely get the item quantity
            item_image_url = self.get_image_url_for_item(item_name)  # Get the image URL for the item

            embed = discord.Embed(
                title=f"{member.display_name}'s Inventory",
                description=f"{item_name}\nQuantity: {item_quantity}",
                color=discord.Colour.random()
            )
            embed.set_image(url=item_image_url)
            embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
            await ctx.send(embed=embed)


    @commands.command(aliases=['give', 'sendsouls'])
    async def pay(self, ctx, member: discord.Member, amount: int):
        sender_id = ctx.author.id
        recipient_id = member.id
        
        # Check if sender has enough balance
        if db.get_balance(sender_id) >= amount:
            db.update_balance(sender_id, -amount)
            db.update_balance(recipient_id, amount)
            db.log_transaction(sender_id, -amount, 'sent')
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

    @commands.command(aliases=['moneytop'])
    async def baltop(self, ctx):
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

    async def create_inventory_image(self, inventory_items):
        # URL of the base inventory image
        base_image_url = "https://raw.githubusercontent.com/ebagcoder/aimeesixbot/main/image/gui/inventory.png"
        
        # Retrieve the base inventory image from the URL
        response = requests.get(base_image_url)
        base_image = Image.open(io.BytesIO(response.content))
        draw = ImageDraw.Draw(base_image)
        font = ImageFont.load_default()  # Load default font
        
        # Define positions for the first slot (you'll need to adjust these)
        start_x, start_y = 10, 10
        slot_width, slot_height = 64, 64  # Update with your slot dimensions
        items_per_row = 9  # Update with the number of slots per row in your image

        # Draw each item name and quantity on the image
        for index, item in enumerate(inventory_items):
            x = start_x + (index % items_per_row) * slot_width
            y = start_y + (index // items_per_row) * slot_height
            item_name = item.get('name', 'Unknown Item')
            item_quantity = item.get('quantity', 0)
            draw.text((x, y), f"{item_name}\n{item_quantity}", fill='black', font=font)

        # Save the edited image to a bytes buffer
        final_buffer = io.BytesIO()
        base_image.save(final_buffer, 'PNG')
        final_buffer.seek(0)

        return final_buffer

    @commands.command(aliases=['inv'])
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        inventory_items = db.get_user_inventory(member.id)  # Fetch inventory items from the database

        # Generate the inventory image with items
        inventory_image_bytes = await self.create_inventory_image(inventory_items)

        # Create a file from the in-memory image
        inventory_image_file = discord.File(fp=inventory_image_bytes, filename='inventory.png')

        # Create the embed with the new image
        embed = discord.Embed(title=f"{member.display_name}'s Inventory", color=discord.Colour.random())
        embed.set_image(url='attachment://inventory.png')
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")

        # Send the embed with the image
        await ctx.send(file=inventory_image_file, embed=embed)

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
