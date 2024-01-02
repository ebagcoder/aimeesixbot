import os
import sys
import discord
from discord.ext import commands
import config

class RestartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def restart(self, ctx):
        # Check if the command invoker is the bot developer
        if ctx.author.id != config.BOT_DEV_ID:
            await ctx.send("You are not authorized to use this command.")
            return

        await ctx.send("Restarting bot...")
        # Close bot connection
        await self.bot.close()
        
        # Restart the bot using execv
        os.execv(sys.executable, ['python'] + sys.argv)

def setup(bot):
    bot.add_cog(RestartCog(bot))
