import discord
from discord.ext import commands

class testcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):

        await ctx.send(f"test")

def setup(bot):
    bot.add_cog(testcog(bot))
