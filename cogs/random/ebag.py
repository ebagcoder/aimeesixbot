from discord.ext import commands
import config

class EbagCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ebag_list = ["Ebay", "Ebaby", "TeaBag", "Ebabith", "Ebagel", "Electronic bag"]

    # Helper method to check if the user has any of the allowed roles
    def user_has_allowed_role(self, user_roles):
        return any(role.id in config.ALLOWED_ROLES for role in user_roles)

    @commands.command()
    async def ebag(self, ctx):
        ebag_message = "Ebag = " + ", ".join(self.ebag_list)
        await ctx.send(ebag_message)

    @commands.command()
    async def addebag(self, ctx, *, new_entry):
        if not self.user_has_allowed_role(ctx.author.roles):
            await ctx.send("You do not have permission to use this command.")
            return

        if new_entry not in self.ebag_list:
            self.ebag_list.append(new_entry)
            await ctx.send(f"'{new_entry}' has been added to the Ebag list.")
        else:
            await ctx.send(f"'{new_entry}' is already in the Ebag list.")

def setup(bot):
    bot.add_cog(EbagCog(bot))
