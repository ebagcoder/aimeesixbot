import discord
from discord.ext import commands, tasks
import sqlite3
from datetime import datetime, timedelta
import random
import asyncio
import db
import config

class Pet:
    def __init__(self, name, image_url, happiness=50, hunger=100, is_alive=True, last_fed=None, last_petted=None, last_search=None):
        self.name = name
        self.image_url = image_url
        self.happiness = happiness
        self.hunger = hunger
        self.is_alive = is_alive
        self.last_fed = last_fed if last_fed else datetime.now()
        self.last_petted = last_petted if last_petted else datetime.now()
        self.last_search = last_search if last_search else datetime.now()

    def feed(self):
        if self.is_alive:
            self.hunger = 100
            self.last_fed = datetime.now()
            self.happiness = min(100, self.happiness + 5)

    def pet(self):
        if self.is_alive:
            self.happiness = min(100, self.happiness + 10)
            self.last_petted = datetime.now()

    def rename(self, new_name):
        self.name = new_name

    def decrease_hunger(self):
        if self.is_alive:
            self.hunger = max(0, self.hunger - random.randint(1, 2))
            if self.hunger == 0:
                self.is_alive = False

    def can_perform_action(self, last_action_time, cooldown_period=timedelta(minutes=5)):
        if last_action_time and datetime.now() - last_action_time < cooldown_period:
            return False
        return True
    
    def get_status(self):
        return {
            'Happiness': self.happiness,
            'Hunger': self.hunger,
            'Is Alive': self.is_alive
        }

    def get_cooldowns(self):
        cooldown_period = timedelta(minutes=5)
        current_time = datetime.now()

        def get_remaining_cooldown(last_action_time):
            if last_action_time is None:
                return 'Ready'
            time_elapsed = current_time - last_action_time
            if time_elapsed < cooldown_period:
                return f'Cooldown ({(cooldown_period - time_elapsed).seconds // 60} min left)'
            return 'Ready'

        # Adjusted the Hunt cooldown calculation
        hunt_cooldown = get_remaining_cooldown(self.last_search)

        return {
            'Feed': get_remaining_cooldown(self.last_fed),
            'Pet': get_remaining_cooldown(self.last_petted),
            'Hunt': hunt_cooldown  # Updated this line
        }
    def hunt(self):
        if not self.is_alive:
            return None, "Your pet is not alive to hunt.", None

        # Define cooldown period
        base_cooldown = timedelta(minutes=30)
        additional_cooldown = timedelta(minutes=30)  # Additional cooldown for high rewards

        if self.last_search and datetime.now() - self.last_search < base_cooldown:
            remaining_time = (self.last_search + base_cooldown) - datetime.now()
            return None, f"Your pet is still tired from the last hunt. Please wait {remaining_time.seconds // 60} minutes.", None

        self.last_search = datetime.now()
        # Random chance to find soul. Higher chance for lower amounts
        soul_found = random.choice([random.randint(1, 499), random.randint(500, 1000)]) 
        high_reward = soul_found > 500
        # If high amount is found, add additional cooldown
        cooldown = base_cooldown if not high_reward else base_cooldown + additional_cooldown
        return soul_found, f"Your pet has returned from the hunt!", cooldown
    
class PetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('pet_data.db')  # Ensure this database file exists and is accessible
        self.cursor = self.db.cursor()
        self.load_pets()  # Ensure this method correctly loads pets from the database
        self.decrease_hunger_loop.start()
        self.available_pets = {
            'bat': {'name': 'Bat', 'image_url': 'https://raw.githubusercontent.com/ebagcoder/aimeesixbot/main/image/pets/PetShopBat.png'},
            'bunny': {'name': 'Bunny', 'image_url': 'https://raw.githubusercontent.com/ebagcoder/aimeesixbot/blob/main/image/pets/PetShopBunny.png'},
            'cat': {'name': 'Cat', 'image_url': 'https://raw.githubusercontent.com/ebagcoder/aimeesixbot/blob/main/image/pets/PetShopCat.png'},
            'mouse': {'name': 'Mouse', 'image_url': 'https://raw.githubusercontent.com/ebagcoder/aimeesixbot/blob/main/image/pets/PetShopMouse.png'}
        }



    def load_pets(self):
        self.cursor.execute('SELECT * FROM pets')
        pets = self.cursor.fetchall()
        self.user_pets = {}
        for pet in pets:
            user_id, name, image_url, happiness, hunger, is_alive, last_fed, last_petted, last_search = pet
            last_fed = datetime.strptime(last_fed, "%Y-%m-%d %H:%M:%S") if last_fed else None
            last_petted = datetime.strptime(last_petted, "%Y-%m-%d %H:%M:%S") if last_petted else None
            last_search = datetime.strptime(last_search, "%Y-%m-%d %H:%M:%S") if last_search else None
            self.user_pets[int(user_id)] = Pet(name, image_url, happiness, hunger, bool(is_alive), last_fed, last_petted, last_search)


    def save_pet(self, user_id, pet):
        is_alive = 1 if pet.is_alive else 0
        last_fed = pet.last_fed.strftime("%Y-%m-%d %H:%M:%S") if pet.last_fed else None
        last_petted = pet.last_petted.strftime("%Y-%m-%d %H:%M:%S") if pet.last_petted else None
        last_search = pet.last_search.strftime("%Y-%m-%d %H:%M:%S") if pet.last_search else None

        self.cursor.execute('''
            REPLACE INTO pets (user_id, name, image_url, happiness, hunger, is_alive, last_fed, last_petted, last_search) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, pet.name, pet.image_url, pet.happiness, pet.hunger, is_alive, last_fed, last_petted, last_search))
        self.db.commit()

    @commands.command(aliases=['pet', 'showmypet'])
    async def show_pets(self, ctx):
        # Display available pets
        for pet_id, pet_info in self.available_pets.items():
            # Convert GitHub URL to raw content URL
            raw_image_url = pet_info['image_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            embed = discord.Embed(title=f"{pet_info['name']}", color=discord.Color.random())
            embed.set_thumbnail(url=raw_image_url)
            embed.set_footer(text="Use the command !adopt_pet (name of the pet) to adopt it.")
            await ctx.send(embed=embed)


    @commands.command(aliases=['adopt', 'adoptapet'])
    async def adopt_pet(self, ctx, *, pet_name: str):
        # Convert pet_name to lowercase and check if it exists in available_pets
        pet_name = pet_name.lower()
        pet_info = next((info for key, info in self.available_pets.items() if info['name'].lower() == pet_name), None)
        
        if pet_info:
            # Check if the author already has a pet
            if ctx.author.id in self.user_pets:
                await ctx.send("You already have a pet!")
                return

            # Create a new Pet instance and add it to the user_pets
            pet = Pet(pet_info['name'], pet_info['image_url'])
            self.user_pets[ctx.author.id] = pet
            self.save_pet(ctx.author.id, pet)
            await ctx.send(f"{ctx.author.display_name} has adopted a {pet_info['name']}!")
        else:
            await ctx.send("Pet not found.")



    @commands.command(aliases=['feed', 'feedmypet'])
    async def feed_pet(self, ctx):
        pet = self.user_pets.get(ctx.author.id)
        if pet:
            if pet.is_alive:
                pet.feed()
                self.save_pet(ctx.author.id, pet)
                await ctx.send(f"{pet.name} has been fed and is now full.")
            else:
                await ctx.send("Sadly, your pet has passed away.")
        else:
            await ctx.send("You don't have a pet yet.")


    @commands.command(aliases=['petmypet'])
    async def pet_pet(self, ctx):
        pet = self.user_pets.get(ctx.author.id)
        if pet:
            if pet.is_alive:
                pet.pet()
                self.save_pet(ctx.author.id, pet)
                await ctx.send(f"You pet {pet.name}.")
            else:
                await ctx.send("Sadly, your pet has passed away.")
        else:
            await ctx.send("You don't have a pet yet.")


    @commands.command(aliases=['renamep', 'renamemypet'])
    async def rename_pet(self, ctx, new_name: str):
        pet = self.user_pets.get(ctx.author.id)
        if pet:
            if pet.is_alive:
                pet.rename(new_name)
                self.save_pet(ctx.author.id, pet)
                await ctx.send(f"Your pet's new name is {new_name}.")
            else:
                await ctx.send("Sadly, your pet is no longer with us.")
        else:
            await ctx.send("You don't have a pet to rename.")

    @commands.command(aliases=['viewmypet'])
    async def view_pet(self, ctx):
        pet = self.user_pets.get(ctx.author.id)
        if pet:
            # Ensure the image URL is a direct link to the raw image file
            raw_image_url = pet.image_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            
            embed = discord.Embed(title=f"{pet.name}'s Stats", color=discord.Color.random())
            embed.set_thumbnail(url=raw_image_url)

            status = pet.get_status()
            cooldowns = pet.get_cooldowns()

            embed.add_field(name="Status", value="\n".join(f"{key}: {value}" for key, value in status.items()), inline=True)
            embed.add_field(name="Cooldowns", value="\n".join(f"{key}: {value}" for key, value in cooldowns.items()), inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have a pet yet.")


    @commands.command()
    async def hunt(self, ctx):
        pet = self.user_pets.get(ctx.author.id)
        if pet:
            soul_found, result_message, cooldown = pet.hunt()  # Adjusted this line
            if soul_found is not None:
                # Ensure the user exists in the database and create if not
                if db.get_user_data(ctx.author.id) is None:
                    db.add_new_user(ctx.author.id)

                # Update the balance of the user in the database
                db.update_balance(ctx.author.id, soul_found)
                new_balance = db.get_balance(ctx.author.id)  # Get updated balance

                # Create an embed to display the hunt earnings
                embed = discord.Embed(
                    title=f"{ctx.author.display_name}'s Pet Found Something!",
                    description=f"{result_message}",
                    color=discord.Color.random()
                )
                embed.add_field(name="Souls Found", value=f"{soul_found} souls", inline=False)
                embed.add_field(name="New Balance", value=f"{new_balance} souls", inline=False)
                embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")

                await ctx.send(embed=embed)
            else:
                await ctx.send(result_message)
        else:
            await ctx.send("You don't have a pet to send on a hunt.")

    @commands.command(aliases=['rsc'])
    async def reset_cooldowns(self, ctx, user: discord.Member = None):
        # If no user is specified, reset the cooldowns for the command author
        target_user = user or ctx.author

        # Find the target user's pet
        pet = self.user_pets.get(target_user.id)
        if pet:
            # Reset the cooldowns
            pet.last_fed = None
            pet.last_petted = None
            pet.last_search = None
            # Save the pet's new state to the database
            self.save_pet(target_user.id, pet)
            await ctx.send(f"All cooldowns for {target_user.display_name}'s pet have been reset.")
        else:
            await ctx.send(f"{target_user.display_name} does not have a pet.")



    @tasks.loop(hours=1)
    async def decrease_hunger_loop(self):
        for user_id, pet in self.user_pets.items():
            pet.decrease_hunger()
            self.save_pet(user_id, pet)


    def cog_unload(self):
        self.decrease_hunger_loop.cancel()
        for user_id, pet in self.user_pets.items():
            self.save_pet(user_id, pet)
        self.db.close()


    @commands.Cog.listener()
    async def on_ready(self):
        print("Pet Cog is ready!")

def setup(bot):
    bot.add_cog(PetCog(bot))
