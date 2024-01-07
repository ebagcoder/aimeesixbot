from discord.ext import commands
import discord
import db
from xp_calculation import calculate_xp, sigmoid_xp_curve
import time
import config
import os
from PIL import Image, ImageDraw


LEVEL_ROLES = {
    1: 'Level 1',
    5: 'Level 5',
    10: 'Level 10',
    25: 'Level 25',
    50: 'Level 50',
    100: 'Level 100'
}

LEVELS_AND_XP = {'0': 0, '1': 100, '2': 255, '3': 475, '4': 770, '5': 1150, '6': 1625, '7': 2205, '8': 2900, '9': 3720, '10': 4675, '11': 5775, '12': 7030, '13': 8450, '14': 10045, '15': 11825, '16': 13800, '17': 15980, '18': 18375, '19': 20995, '20': 23850, '21': 26950, '22': 30305, '23': 33925, '24': 37820, '25': 42000, '26': 46475, '27': 51255, '28': 56350, '29': 61770, '30': 67525, '31': 73625, '32': 80080, '33': 86900, '34': 94095, '35': 101675, '36': 109650, '37': 118030, '38': 126825, '39': 136045, '40': 145700, '41': 155800, '42': 166355, '43': 177375, '44': 188870, '45': 200850, '46': 213325, '47': 226305, '48': 239800, '49': 253820, '50': 268375, '51': 283475, '52': 299130, '53': 315350, '54': 332145, '55': 349525, '56': 367500, '57': 386080, '58': 405275, '59': 425095, '60': 445550, '61': 466650, '62': 488405, '63': 510825, '64': 533920, '65': 557700, '66': 582175, '67': 607355, '68': 633250, '69': 659870, '70': 687225, '71': 715325, '72': 744180, '73': 773800, '74': 804195, '75': 835375, '76': 867350, '77': 900130, '78': 933725, '79': 968145, '80': 1003400, '81': 1039500, '82': 1076455, '83': 1114275, '84': 1152970, '85': 1192550, '86': 1233025, '87': 1274405, '88': 1316700, '89': 1359920, '90': 1404075, '91': 1449175, '92': 1495230, '93': 1542250, '94': 1590245, '95': 1639225, '96': 1689200, '97': 1740180, '98': 1792175, '99': 1845195, '100': 1899250}
MAX_LEVEL = 100



class Leveling(commands.Cog):
    command_xp_enabled = True
    disabled_xp_channels = set()
    def __init__(self, bot):
        self.bot = bot

    def has_allowed_role(self, ctx):
        # Fetch the allowed role IDs from config
        allowed_role_ids = config.ALLOWED_ROLES

        # Get the role IDs of the user
        user_role_ids = [role.id for role in ctx.author.roles]

        # Check if the user has any of the allowed roles
        return any(role_id in user_role_ids for role_id in allowed_role_ids)



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_data = db.get_user_data(message.author.id)
        if not user_data:
            db.add_new_user(message.author.id)
            current_xp, current_level, last_message_timestamp, current_balance, last_daily_claim = 0, 0, 0, 0, None
        else:
            # Update this line to match the actual number of elements in user_data
            _, current_xp, current_level, last_message_timestamp, current_balance, last_daily_claim = user_data

        current_level = int(current_level)  # Ensure current_level is an integer
        new_xp = calculate_xp(message.content, last_message_timestamp)
        new_total_xp = current_xp + new_xp
        db.update_user_xp(message.author.id, new_total_xp, int(time.time()))

        new_level = self.find_level(new_total_xp)
        if new_level > current_level:
            await self.handle_level_up(message.author, new_level)

    async def handle_level_up(self, member, new_level):
        db.update_user_level(member.id, new_level)
        level_up_channel = self.bot.get_channel(config.LEVEL_UP_CHANNEL_ID)
        if level_up_channel:
            await level_up_channel.send(f"Congratulations {member.mention}, you have reached level {new_level}!")
        else:
            await member.send(f"Congratulations, you have reached level {new_level}!")
        await self.assign_level_role(member, new_level)

    async def assign_level_role(self, member, new_level):
        guild = member.guild
        roles_to_add = []

        for level, role_name in LEVEL_ROLES.items():
            if level <= new_level:
                role = discord.utils.get(guild.roles, name=role_name)
                if role and role not in member.roles:
                    roles_to_add.append(role)

        if roles_to_add:
            await member.add_roles(*roles_to_add)
            print(f"Added roles for levels up to {new_level} to {member.display_name}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if the message is in a channel where XP is disabled
        if message.channel.id in Leveling.disabled_xp_channels:
            return

        # Check if the message starts with the command prefix and if command XP is disabled
        if not Leveling.command_xp_enabled and message.content.startswith('!'):  # Assuming '!' is your command prefix
            return
        

    @commands.command(name='togglecommandxp')
    async def toggle_command_xp(self, ctx):
        if not self.has_allowed_role(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        # Toggle the state
        Leveling.command_xp_enabled = not Leveling.command_xp_enabled

        # Confirm the action to the user
        state = "enabled" if Leveling.command_xp_enabled else "disabled"
        await ctx.send(f"XP from command messages has been {state}.")


    @commands.command(aliases=['setlvl'])
    async def setlevel(self, ctx, member: discord.Member, level: int):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        if level < 0 or level > MAX_LEVEL:
            await ctx.send("Invalid level. Please enter a level between 0 and 100.")
            return

        # Set the user's level
        required_xp = LEVELS_AND_XP[str(level)]
        db.update_user_level(member.id, level)
        db.update_user_xp(member.id, required_xp, int(time.time()))

        # Send confirmation message
        await ctx.send(f"{member.display_name}'s level has been set to {level} with {required_xp} XP.")
        
        # Assign roles based on the new level
        await self.assign_level_role(member, level)

    @commands.command(name='toggle_channel_xp')
    async def toggle_channel_xp(self, ctx, channel_id: int):
        if not self.has_allowed_role(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        # Toggle the XP state for the channel
        if channel_id in Leveling.disabled_xp_channels:
            Leveling.disabled_xp_channels.remove(channel_id)
            state = "enabled"
        else:
            Leveling.disabled_xp_channels.add(channel_id)
            state = "disabled"

        # Confirm the action to the user
        await ctx.send(f"XP earning in <#{channel_id}> has been {state}.")

    # Error handler for the toggle_channel_xp command
    @toggle_channel_xp.error
    async def toggle_channel_xp_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid channel ID.")
        else:
            raise error


    def calculate_xp(self, message_content, last_message_timestamp):
        words = message_content.split()
        word_count = len(words)
        xp_per_word = 2 if word_count > 10 else 1
        xp_from_message = xp_per_word * word_count

        # Time check for XP cap (250 XP per minute)
        current_time = int(time.time())
        if current_time - last_message_timestamp < 60:
            xp_from_message = min(xp_from_message, 250)

        return xp_from_message

    def find_level(self, current_total_xp):
        for level, xp_needed in LEVELS_AND_XP.items():
            if current_total_xp < int(xp_needed):
                return int(level) - 1
        return MAX_LEVEL


    def calculate_level_progress(self, current_xp, current_level):
        # Logic to calculate progress towards the next level
        current_level_xp = LEVELS_AND_XP[str(current_level)]
        next_level_xp = LEVELS_AND_XP[str(current_level + 1)] if current_level < MAX_LEVEL else current_xp
        xp_progressed = current_xp - current_level_xp
        xp_needed_for_next_level = next_level_xp - current_level_xp
        progress_percentage = (xp_progressed / xp_needed_for_next_level) if xp_needed_for_next_level else 1
        return progress_percentage

    def create_horizontal_progress_image(self, width, height, progress, fg_color, bg_color, save_path):
        # Make sure the folder exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Create a new image with a background color
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        # Calculate the width of the filled part
        fill_width = int(width * progress)
        # Draw the filled part
        draw.rectangle([(0, 0), (fill_width, height)], fill=fg_color)
        # Save the image
        image.save(save_path)

    @commands.command(aliases=['exp'])
    async def xp(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_data = db.get_user_data(member.id)

        if not user_data:
            await ctx.send(f"{member.display_name} does not have any XP yet.")
            return

        # Unpack all values from user_data, assuming it returns 6 values.
        _, current_xp, current_level, _, _, _ = user_data
        current_level = int(current_level)  # Convert current_level to an integer.
        progress = self.calculate_level_progress(current_xp, current_level)
        progress_percentage = progress * 100

        # Define the path where your progress bar image is stored.
        image_folder_path = 'image/'  # The folder path to your image folder.
        progress_bar_image_name = 'progress_bar.png'
        progress_bar_image_path = os.path.join(image_folder_path, progress_bar_image_name)

        # Generate the progress bar image.
        self.create_horizontal_progress_image(400, 40, progress, 'green', 'grey', progress_bar_image_path)

        # Make sure the image file exists.
        if not os.path.exists(progress_bar_image_path):
            await ctx.send("Progress bar image not found.")
            return

        # Calculate XP for the next level, handling max level case.
        if current_level >= MAX_LEVEL:
            xp_for_next_level = 0
        else:
            next_level_xp = LEVELS_AND_XP[str(current_level + 1)]
            xp_for_next_level = next_level_xp - current_xp

        # Create the embed for the message.
        embed = discord.Embed(
            title=f"{member.display_name}'s Level Stats",
            color=discord.Colour.random()
        )
        embed.add_field(name="Current Level", value=str(current_level), inline=True)
        embed.add_field(name="Current XP", value=str(current_xp), inline=True)
        embed.add_field(name="XP for Next Level", value=str(xp_for_next_level), inline=True)
        embed.add_field(name="Progress", value=f"{progress_percentage:.2f}%", inline=False)
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")

        # Send the embed with the progress bar image.
        file = discord.File(progress_bar_image_path, filename='progress_bar.png')
        embed.set_image(url="attachment://progress_bar.png")
        await ctx.send(embed=embed, file=file)

    @commands.command()
    async def createlevelroles(self, ctx):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        # Create roles in descending order starting with the highest level
        for level in sorted(LEVEL_ROLES.keys(), reverse=True):
            role_name = LEVEL_ROLES[level]
            existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
            if existing_role is None:
                await ctx.guild.create_role(name=role_name, color=discord.Color.orange())
                await ctx.send(f"Created role '{role_name}' with orange color.")
            else:
                await ctx.send(f"The role '{role_name}' already exists.")



    

    @commands.command(aliases=['resetexp'])
    async def resetxp(self, ctx, member: discord.Member):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        # Check if the user exists in the database
        user_data = db.get_user_data(member.id)
        if not user_data:
            await ctx.send(f"{member.display_name} is not in the database.")
            return

        # Reset the user's XP and level
        db.update_user_xp(member.id, 0, int(time.time()))
        db.update_user_level(member.id, 0)

        # Remove level roles
        roles_to_remove = [discord.utils.get(ctx.guild.roles, name=role_name) for level, role_name in LEVEL_ROLES.items()]
        roles_to_remove = [role for role in roles_to_remove if role is not None and role in member.roles]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        await ctx.send(f"{member.display_name}'s XP has been reset to 0, their level has been set to 0, and level roles have been removed.")


    @commands.command(aliases=['leveltop'])
    async def leadb(self, ctx):
        top_users = db.get_top_users(10)
        if not top_users:
            await ctx.send("Leaderboard is currently empty.")
            return

        leaderboard_description = ""
        for idx, (user_id, user_xp, user_level) in enumerate(top_users):
            user = ctx.guild.get_member(user_id)  # Try to get the member from the guild
            if user:
                display_name = user.display_name  # Use member's display name
            else:
                try:
                    user = await self.bot.fetch_user(user_id)  # Fetch user from Discord's API
                    display_name = user.name  # Use user's name
                except:
                    display_name = f"User ID {user_id}"  # Fallback if the user cannot be fetched

            leaderboard_description += f"{idx + 1}. {display_name} - Level: {user_level}, XP: {user_xp}\n"

        embed = discord.Embed(
            title="🏆 Level Leaderboard 🏆",
            description=leaderboard_description,
            color=discord.Colour.random()
        )
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
        await ctx.send(embed=embed)


    @commands.command()
    async def deletelevelroles(self, ctx):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        # Iterate through the roles
        for level in LEVEL_ROLES:
            role_name = LEVEL_ROLES[level]
            # Check if the role exists
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role:
                await role.delete()
                await ctx.send(f"Deleted role '{role_name}'.")
            else:
                await ctx.send(f"The role '{role_name}' does not exist.")

        await ctx.send("All specified level roles have been deleted.")


    @commands.command(aliases=['addexp'])
    async def addxp(self, ctx, member: discord.Member, xp: int):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        user_data = db.get_user_data(member.id)
        if not user_data:
            await ctx.send(f"{member.display_name} is not in the database.")
            return

        _, current_xp, current_level, _ = user_data
        new_total_xp = current_xp + xp
        db.update_user_xp(member.id, new_total_xp, int(time.time()))

        new_level = self.find_level(new_total_xp)
        if new_level > current_level:
            await self.handle_level_up(member, new_level)
        else:
            await ctx.send(f"Added {xp} XP to {member.display_name}. They are now at {new_total_xp} XP.")

    @commands.command(aliases=['removeexp'])
    async def removexp(self, ctx, member: discord.Member, xp: int):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        user_data = db.get_user_data(member.id)
        if not user_data:
            await ctx.send(f"{member.display_name} is not in the database.")
            return

        _, current_xp, current_level, _ = user_data
        new_total_xp = max(current_xp - xp, 0)
        db.update_user_xp(member.id, new_total_xp, int(time.time()))

        new_level = self.find_level(new_total_xp)
        if new_level < current_level:
            await self.handle_level_up(member, new_level)
        else:
            await ctx.send(f"Removed {xp} XP from {member.display_name}. They are now at {new_total_xp} XP.")


def setup(bot):
    bot.add_cog(Leveling(bot))