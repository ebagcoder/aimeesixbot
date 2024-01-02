import discord
from discord.ext import commands
import db
import time
import config

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def daily(self, ctx):
        user_id = ctx.author.id
        user_data = db.get_user_data(user_id)

        if not user_data:
            db.add_new_user(user_id)
            user_data = (user_id, 0, 0, 0, 0, 0)

        _, _, _, _, current_balance, last_daily_claim = user_data

        # Check if 24 hours have passed since the last claim
        if last_daily_claim is None or (time.time() - last_daily_claim) >= 86400:
            daily_reward = 100  # Amount of coins to award
            db.update_balance(user_id, daily_reward)
            db.update_last_daily_claim(user_id, int(time.time()))

            embed = discord.Embed(
                title="Daily Reward",
                description=f"You have claimed your daily reward of {daily_reward} souls!",
                color=discord.Colour.random()
            )
            embed.set_footer(text="This bot was made by ebagcoder for AimeeSixx")
            await ctx.send(embed=embed)
        else:
            await ctx.send("You have already claimed your daily reward. Come back tomorrow!")

    @commands.command()
    async def resetdaily(self, ctx, member: discord.Member):
        # Check if the user has the allowed role
        if any(role.id in config.ALLOWED_ROLES for role in ctx.author.roles):
            # Reset the last daily claim time to None (or 0)
            db.update_last_daily_claim(member.id, None)  # or 0, depending on how your system is set up

            await ctx.send(f"The daily timer for {member.display_name} has been reset.")
        else:
            await ctx.send("You do not have permission to use this command.")


def setup(bot):
    bot.add_cog(Daily(bot))
