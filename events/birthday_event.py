# events/birthday_event.py
import discord
import sqlite3
import asyncio
from datetime import datetime
from config import BIRTHDAY_CHANNEL_ID

async def check_birthdays(bot):
    await bot.wait_until_ready()
    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)
    if not channel:
        print("Birthday channel not found.")
        return

    while not bot.is_closed():
        # Get today's date in the format YYYY/MM/DD
        today = datetime.now().strftime("%Y/%m/%d")
        
        # Connect to the database and check for birthdays
        conn = sqlite3.connect('birthdays.db')
        c = conn.cursor()
        c.execute("SELECT member_id FROM birthdays WHERE date = ?", (today,))
        birthdays = c.fetchall()
        conn.close()

        for member_id in birthdays:
            member = bot.get_user(member_id[0])
            if member:
                embed = discord.Embed(
                    title="🎉 Happy Birthday! 🎉",
                    description=f"Happy Birthday {member.mention}! 🥳",
                    color=discord.Colour.random()
                )
                embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
                await channel.send(embed=embed)
        
        # Wait for 24 hours before checking again
        await asyncio.sleep(86400)  # 86400 seconds in a day

async def setup(bot):
    bot.loop.create_task(check_birthdays(bot))
