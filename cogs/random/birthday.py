import discord
from discord.ext import commands
import sqlite3
import random
from config import ALLOWED_ROLES, BIRTHDAY_CHANNEL_ID

class BirthdayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_check(self, roles):
        # Check if any of the user's roles match the allowed role IDs
        return any(role.id in ALLOWED_ROLES for role in roles)

    def channel_check(self, ctx):
        # Check if the command is used in the specified channel
        return ctx.channel.id == BIRTHDAY_CHANNEL_ID

    @commands.command()
    async def setuserbday(self, ctx, date_str, member: discord.Member):
        if not self.role_check(ctx.author.roles):
            await ctx.send("You do not have permission to use this command.")
            return

        if not self.channel_check(ctx):
            await ctx.send("This command can only be used in a specific channel.")
            return

        # Validate and parse the date
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            await ctx.send("Invalid date format. Please use YYYY-MM-DD.")
            return

        # Format the date in the desired output format
        formatted_date = date_obj.strftime("%Y/%m/%d")

        # Connect to the database and insert/update the birthday
        conn = sqlite3.connect('birthdays.db')
        c = conn.cursor()
        c.execute("REPLACE INTO birthdays (member_id, date) VALUES (?, ?)", (member.id, formatted_date))
        conn.commit()
        conn.close()

        await ctx.send(f"Birthday for {member.mention} set to {formatted_date}.")

    @commands.command()
    async def removebday(self, ctx, member: discord.Member):
        if not self.role_check(ctx.author.roles):
            await ctx.send("You do not have permission to use this command.")
            return

        if not self.channel_check(ctx):
            await ctx.send("This command can only be used in a specific channel.")
            return

        conn = sqlite3.connect('birthdays.db')
        c = conn.cursor()
        c.execute("DELETE FROM birthdays WHERE member_id = ?", (member.id,))
        conn.commit()
        conn.close()

        await ctx.send(f"Birthday for {member.mention} removed.")

    @commands.command()
    async def birthday(self, ctx, date, member: discord.Member):
        if not self.channel_check(ctx):
            await ctx.send("This command can only be used in a specific channel.")
            return

        conn = sqlite3.connect('birthdays.db')
        c = conn.cursor()
        c.execute("SELECT date FROM birthdays WHERE member_id = ?", (member.id,))
        birthday = c.fetchone()
        conn.close()

        if birthday:
            await ctx.send(f"Birthday information for {member.mention}: {birthday[0]}")
        else:
            await ctx.send(f"No birthday information found for {member.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)  # Restrict this command to administrators
    async def test_birthday_ping(self, ctx, member: discord.Member):
        # This command simulates a birthday announcement for the specified member
        random_color = discord.Colour(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(
            title="🎉 Happy Birthday! 🎉",
            url="https://github.com/ebagcoder",
            description=f"Happy Birthday {member.mention}! 🥳",
            color=random_color
        )
        embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
        birthday_channel = self.bot.get_channel(BIRTHDAY_CHANNEL_ID)
        if birthday_channel:
            await birthday_channel.send(embed=embed)
        else:
            await ctx.send("Birthday channel not found.")
def setup(bot):
    bot.add_cog(BirthdayCog(bot))
