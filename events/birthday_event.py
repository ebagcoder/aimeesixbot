import discord
import sqlite3
import asyncio
from datetime import datetime
from config import BIRTHDAY_CHANNEL_ID, BIRTHDAY_ROLE

async def check_birthdays(bot):
    await bot.wait_until_ready()
    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)
    if not channel:
        print("Birthday channel not found.")
        return

    while not bot.is_closed():
        today = datetime.now().strftime("%Y/%m/%d")
        
        # Connect to the database and check for birthdays
        conn = sqlite3.connect('birthdays.db')
        c = conn.cursor()
        c.execute("SELECT member_id FROM birthdays WHERE date = ?", (today,))
        birthdays_today = {row[0] for row in c.fetchall()}  # Use a set for efficient lookup
        c.execute("SELECT member_id FROM birthdays")
        all_birthdays = {row[0] for row in c.fetchall()}
        conn.close()

        for guild in bot.guilds:
            birthday_role = discord.utils.get(guild.roles, name=BIRTHDAY_ROLE)
            if not birthday_role:
                print(f"Birthday role '{BIRTHDAY_ROLE}' not found in guild '{guild.name}'")
                continue

            for member in guild.members:
                if member.id in birthdays_today:
                    if birthday_role not in member.roles:
                        await member.add_roles(birthday_role)
                        embed = discord.Embed(
                            title="🎉 Happy Birthday! 🎉",
                            description=f"Happy Birthday {member.mention}! 🥳",
                            color=discord.Colour.random()
                        )
                        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
                        await channel.send(embed=embed)
                elif member.id in all_birthdays and birthday_role in member.roles:
                    await member.remove_roles(birthday_role)

        # Wait for 24 hours before checking again
        await asyncio.sleep(86400)  # 86400 seconds in a day

async def setup(bot):
    bot.loop.create_task(check_birthdays(bot))
