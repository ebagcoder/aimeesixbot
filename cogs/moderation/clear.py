from discord.ext import commands
import discord
import config
import asyncio
import re

class clearCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_allowed(self, user):
        """Check if the user has any of the allowed roles."""
        return any(role.id in config.ALLOWED_ROLES for role in user.roles)

    @commands.command(aliases=['delmsgs'])
    async def clear(self, ctx, number: int):
        """
        Delete a specified number of messages.
        :param ctx: Context for the command.
        :param number: Number of messages to delete.
        """
        if not await self.is_allowed(ctx.author):
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
            await ctx.send(f"Error: {str(e)}")

def setup(bot):
    bot.add_cog(clearCommands(bot))
