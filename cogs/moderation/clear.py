from discord.ext import commands
import discord
import config
import asyncio
import re
from discord.ext.commands import CheckFailure


class clearCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_allowed_role(self, ctx):
        # Fetch the allowed role IDs from config
        allowed_role_ids = config.ALLOWED_ROLES

        # Get the role IDs of the user
        user_role_ids = [role.id for role in ctx.author.roles]

        # Check if the user has any of the allowed roles
        return any(role_id in user_role_ids for role_id in allowed_role_ids)

    @commands.command(aliases=['delmsgs'])
    async def clear(self, ctx, number: int):
        if not self.has_allowed_role(ctx):
            await ctx.send("You don't have permission to use this command.")
            return

        if number < 1:
            await ctx.send("You need to specify a number greater than 0!")
            return

        try:
            messages = await ctx.channel.history(limit=number + 1).flatten()
            await ctx.channel.delete_messages(messages)
            confirmation = await ctx.send(f"Deleted {number} messages!")
            await confirmation.delete(delay=5)
        except Exception as e:
            # Optionally log the exception here
            await ctx.send(f"Error: {str(e)}")


def setup(bot):
    bot.add_cog(clearCommands(bot))
