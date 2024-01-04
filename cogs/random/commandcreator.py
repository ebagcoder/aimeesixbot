from discord.ext import commands
import discord
import json
import os
import config


class SimpleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_file = 'custom_commands.json'
        self.custom_commands = self.load_commands()

    def load_commands(self):
        if not os.path.exists(self.commands_file):
            return {}
        with open(self.commands_file, 'r') as file:
            return json.load(file)

    def save_commands(self):
        with open(self.commands_file, 'w') as file:
            json.dump(self.custom_commands, file, indent=4)

    def add_command(self, name, response):
        async def new_command(ctx):
            await ctx.send(response)
        new_command.__name__ = name
        cmd = commands.Command(new_command, name=name)
        self.bot.add_command(cmd)
        self.custom_commands[name] = response

    @commands.command(aliases=['newcommand'])
    async def create_command(self, ctx, command_name: str, *, response: str):
        if not any(role.id in config.ALLOWED_ROLES for role in ctx.author.roles):
            await ctx.send("You do not have permission to use this command.")
            return

        if command_name in self.custom_commands:
            await ctx.send(f"A command with the name '{command_name}' already exists.")
            return

        self.add_command(command_name, response)
        self.save_commands()
        await ctx.send(f"Command '{command_name}' created.")

    @commands.Cog.listener()
    async def on_ready(self):
        for name, response in self.custom_commands.items():
            self.add_command(name, response)

def setup(bot):
    bot.add_cog(SimpleCommands(bot))
