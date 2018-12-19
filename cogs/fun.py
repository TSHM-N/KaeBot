import discord
from discord.ext import commands
import random, asyncio


class Fun:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vaporwave", brief="Vaporwave some text!", description="Vaporwave inputted text.",
                      aliases=["vapourwave"])
    async def vaporwave(self, ctx, *, text: str):
        vaporwaved = ""
        for character in text:
            if character == " ":
                vaporwaved += "  "
                continue
            vaporwaved += chr(0xFEE0 + ord(character))
        await ctx.send(vaporwaved)

    @commands.command(name="slap", brief="Slap someone!", description="Slap someone!")
    async def slap(self, ctx, user: discord.Member, *, reason: str = ""):
        if reason:
            await ctx.send(f"{user.mention} just got slapped by {ctx.message.author.mention}! Reason: '{reason}'.")
        else:
            await ctx.send(f"{user.mention} just got slapped by {ctx.message.author.mention}!")

    @commands.command(name="pat", brief="Pat someone on the head.",
                      description="Pat someone on the head.")
    async def pat(self, ctx, user: discord.Member, *, reason: str = ""):
        if reason:
            await ctx.send(f"{ctx.author.mention} gently pats {user.mention} and says '{reason}'.")
        else:
            await ctx.send(f"{ctx.author.mention} gently pats {user.mention}.")

    @commands.command(name="hotornot", brief="Check the hotness of someone.",
                      description="Check someone's hotness; defaults to you if no argument is provided.")
    async def hotornot(self, ctx, user: commands.MemberConverter = None):
        if not user:
            user = ctx.author
        rawasciinum = 0
        for char in list(user.name):
            rawasciinum += ord(char)
        hotness = rawasciinum % 100
        if hotness >= 90:
            message = "They're a registered QT3.14!"
        elif hotness >= 80:
            message = "Great by Sacred Heart standards!"
        elif hotness >= 60:
            message = "Definitely dating material."
        elif hotness >= 40:
            message = "Maybe not the best, but definitely not the worst!"
        elif hotness >= 20:
            message = "Yikes."
        elif hotness >= 5:
            message = "Ouch..."
        else:
            message = "You better have a *really* good personality, bud."

        await ctx.send(f"{user.mention} is `{hotness}%` hot. {message}")

    @commands.command(name="lovecalculator", brief="Calculate the love percentage of two people.",
                      description="Calculate the love percentage of two people.", aliases=["lovecalc"])
    async def lovecalculator(self, ctx, user1: discord.Member, user2: discord.Member):
        if user1 == user2:
            return await ctx.send("You can't calculate love between the same person.")
        shipname = (user1.name[:len(user1.name) // 2] + user2.name[len(user2.name) // 2:]).capitalize()
        user1raw = 0
        for char in list(user1.name):
            user1raw += ord(char)
        user2raw = 0
        for char in list(user2.name):
            user2raw += ord(char)

        love = (user1raw + user2raw) % 100
        await ctx.send(f"{user1.mention} & {user2.mention} (ship name: {shipname}) have a love percentage of {love}%!")

    @commands.command(name="russianroulette", brief="Play a quick game of Russian Roulette.",
                      description="Play a game of Russian Roulette.\n Choose the number of bullets in your barrel "
                                  "(default: 1), spin the barrel and fire.", aliases=["rr"])
    async def russianroulette(self, ctx, bullets: int = 1):
        if bullets in range(0, 7):
            if bullets == 0:
                await ctx.send("Huh? That's not Russian Roulette, you pussy.")
            elif bullets == 6:
                await ctx.send("Do you have a death wish or something?")
            else:
                if random.random() < (bullets / 6):
                    await ctx.send("You took a bullet to the head. Better luck next time!")
                else:
                    await ctx.send("You survived! You live to play another day.")
        else:
            await ctx.send("That's not an appropriate number of bullets.")

    @commands.command(name="banroulette", brief="Play a quick game of Ban Roulette.",
                      description="Play a game of Ban Roulette.\n Choose the number of bullets in your barrel "
                                  "(default: 1), spin the barrel and fire.\n However, the difference between this and"
                                  " normal Russian Roulette is that if you die in this mode, you get banned!\n Be care"
                                  "ful!", aliases=["br"])
    async def banroulette(self, ctx, bullets: int = 1):
        if bullets in range(0, 7):
            if bullets == 0:
                await ctx.send("Huh? That's not Russian Roulette, you pussy.")
            elif bullets == 6:
                await ctx.send("Do you want to get banned or something?")
            else:
                if random.random() < (bullets / 6):
                    await ctx.send("Sorry chief, but you died! You have five seconds to say your goodbyes before you"
                                   " get banned.")
                    await asyncio.sleep(5)
                    await ctx.send(f"{ctx.message.author} has been banned. Their ID: {ctx.message.author.id}")
                    await ctx.message.author.ban(reason="You failed Ban Roulette.", delete_message_days=0)
                else:
                    await ctx.send("You survived Ban Roulette! Nice job.")
        else:
            await ctx.send("That's not an appropriate number of bullets.")


def setup(bot):
    bot.add_cog(Fun(bot))
