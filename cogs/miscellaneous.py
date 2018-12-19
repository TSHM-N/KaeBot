import discord
from discord.ext import commands
import random, asyncio


class Miscellaneous:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="random", brief="Generates a random number between 'start' and 'end'. Int only.",
                      description="Generates a random int between int 'start' and int 'end' such that "
                                  "'start <= n <= end'. Only accepts int arguments.")
    async def random(self, ctx, start: int, end: int):
        await ctx.send(f"Your number is: {random.randint(start, end)}.")

    @commands.command(name="flip", brief="Flips a coin.", description="Flips a coin and returns the result.")
    async def flip(self, ctx):
        if random.randint(1, 2) == 1:
            await ctx.send("Heads.")
        else:
            await ctx.send("Tails.")

    @commands.command(name="getinvite", brief="Invite KaeBot to your server.",
                      description="Gets two invites (one with admin permissions, and one without) that allows you"
                                  " to bring KaeBot to your server.")
    async def getinvite(self, ctx):
        embed = discord.Embed(
            title="Invite KaeBot to your server!",
            colour=discord.Color.from_rgb(81, 0, 124)
        )
        embed.set_thumbnail(url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.add_field(name="Non-admin invite link",
                        value="If you want to add KaeBot to your server without giving it administrative permissions, "
                              "click the following link:\n https://discordapp.com/oauth2/authorize?client_id=49443105"
                              "6297197568&scope=bot&permissions=0",
                        inline=False)
        embed.add_field(name="Admin invite link",
                        value="If you want to add KaeBot to your server and give it administrative permissions, "
                              "click the following link:\n https://discordapp.com/oauth2/authorize?client_id=49443105"
                              "6297197568&scope=bot&permissions=8",
                        inline=False)
        embed.add_field(name="Warning:",
                        value="Note that both of these links require you to have at least the 'Manage Server' "
                              "permission for the server you want to invite KaeBot to.",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="rift", brief="Creates a rift between one channel and another.",
                      description="Opens a rift between the channel the command is executed in and the target channel."
                                  "\nThis rift transmits all messages made by you to the target channel until closed.")
    async def rift(self, ctx, targetchannel: discord.TextChannel):
        await ctx.send("Rift opened! Type .close. to close the rift.")
        while True:
            message = await self.bot.wait_for("message",
                                              check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if message.content == ".close.":
                await ctx.send("Rift closed.")
                break
            else:
                await targetchannel.send(f"{ctx.author.name} speaks from a rift: '{message.content}'")

    @commands.command(name="ping", brief="Pong!",
                      description="Pings the bot and gets websocket latency.")
    async def ping(self, ctx):
        await ctx.send(f"Pong! Latency: {self.bot.latency * 1000:.2f}ms")

    @commands.command(name="countdown", brief="Start a countdown to 0 (30 seconds max).",
                      description="Start a countdown going down to 0. The maximum start value is 30 seconds.")
    async def countdown(self, ctx, seconds: int):
        if seconds <= 0:
            await ctx.send("The countdown start can't be 0 or less!")
        elif seconds > 30:
            await ctx.send("That value is too big (<30).")
        else:
            while seconds != 0:
                await ctx.send(f"{seconds}...")
                await asyncio.sleep(1)
                seconds -= 1
            await ctx.send("Go!")


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
