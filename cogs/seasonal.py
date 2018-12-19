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
            try:
                if not ctx.message.author.nick.endswith("\U0001f383"):
                    if ctx.message.author.nick.endswith(
                        "\U0001f384"
                    ):  # If already ends with Christmas emoji
                        changednick = ctx.message.author.nick[:-1] + " \U0001f383"
                    else:
                        changednick = ctx.message.author.nick + " \U0001f383"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send(f"Your nickname is now '{changednick}'.")
                else:
                    await ctx.send("Your nickname is already spooky!")

            except AttributeError:  # except if the person has no nick, because endswith is null
                if not ctx.message.author.name.endswith("\U0001f383"):
                    if ctx.message.author.name.endswith(
                        "\U0001f384"
                    ):  # If already ends with Christmas emoji
                        changednick = ctx.message.author.name[:-1] + " \U0001f383"
                    else:
                        changednick = ctx.message.author.name + " \U0001f383"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send(f"Your nickname is now '{changednick}'.")
                else:
                    await ctx.send("Your nickname is already spooky!")
        else:
            await ctx.send("It's not October, you can't use this yet!")

    @commands.command(
        name="christmas",
        brief="Adds some christmas spirit to your nickname.",
        description="Adds a Christmas tree to your nickname. Only usable during December!",
    )
    async def christmas(self, ctx):
        if datetime.datetime.today().month == 12:
            try:
                if not ctx.message.author.nick.endswith("\U0001f384"):
                    if ctx.message.author.nick.endswith(
                        "\U0001f383"
                    ):  # If already ends with Spooky emoji
                        changednick = ctx.message.author.nick[:-1] + " \U0001f384"
                    else:
                        changednick = ctx.message.author.nick + " \U0001f384"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send(f"Your nickname is now '{changednick}'.")
                else:
                    await ctx.send("Your nickname is already Christmassy!")

            except AttributeError:  # except if the person has no nick, because endswith is null
                if not ctx.message.author.name.endswith("\U0001f384"):
                    if ctx.message.author.name.endswith(
                        "\U0001f383"
                    ):  # If already ends with Spooky emoji
                        changednick = ctx.message.author.name[:-1] + " \U0001f384"
                    else:
                        changednick = ctx.message.author.name + " \U0001f384"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send(f"Your nickname is now '{changednick}'.")
                else:
                    await ctx.send("Your nickname is already Christmassy!")
        else:
            await ctx.send("It's not December, you can't use this yet!")


def setup(bot):
    bot.add_cog(Seasonal(bot))
