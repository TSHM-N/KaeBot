import discord
from discord.ext import commands
import datetime


class Seasonal:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="spooky",
        brief="Adds some spook to your nickname.",
        description="Adds a pumpkin to your nickname. Only usable during October!",
    )
    async def spooky(self, ctx):
        if datetime.datetime.today().month == 10:
            if ctx.message.author.display_name.endswith("\U0001f383"):
                await ctx.send("Your nickname is already spooky!")
            else:
                await ctx.message.author.edit(nick=ctx.message.author.display_name + " \U0001f383")
                await ctx.send(f"Your nickname is now '{ctx.author.display_name}'.")
        else:
            await ctx.send("You can't use this yet...")

    @commands.command(
        name="christmas",
        brief="Adds some christmas spirit to your nickname.",
        description="Adds a Christmas tree to your nickname. Only usable during December!",
    )
    async def christmas(self, ctx):
        if datetime.datetime.today().month == 12:
            if ctx.message.author.display_name.endswith("\U0001f384"):
                await ctx.send("Your nickname is already Christmassy!")
            else:
                await ctx.message.author.edit(nick=ctx.message.author.display_name + " \U0001f384")
                await ctx.send(f"Your nickname is now '{ctx.author.display_name}'.")
        else:
            await ctx.send("You can't use this yet...")


def setup(bot):
    bot.add_cog(Seasonal(bot))
