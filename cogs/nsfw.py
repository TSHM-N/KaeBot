import discord
from discord.ext import commands
import aiohttp, json, random, xmltodict


class NSFW:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rule34", brief="Search rule34.xxx for a tag or tags.",
                      description="Search rule34.xxx for one or more tags and return a post.\n Aliased to r34.",
                      aliases=["r34"])
    async def rule34(self, ctx, *, tags):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=f"{self.bot.KAEBOT_VERSION} | Searched tags: {tags}")
        embed.set_author(name=f"Random result for '{tags}':", icon_url=self.bot.user.avatar_url)
        if ctx.channel.is_nsfw():
            async with ctx.channel.typing():
                async with aiohttp.ClientSession() as session:
                    posturl = f"https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tags.replace(' ', '+')}&limit=100"
                    async with session.post(posturl) as response:
                        postdict = json.loads(json.dumps(xmltodict.parse((await response.read()).decode("utf-8"))))
                        try:
                            randompost = random.choice(postdict["posts"]["post"])
                        except KeyError:
                            return await ctx.send("No results found.")
                        embed.set_image(url=randompost["@file_url"])
                        await ctx.send(embed=embed)
        else:
            await ctx.send("\U00002757This command cannot execute in a non-NSFW channel.\n"
                           "Try using this command in an NSFW channel (or set this channel to NSFW if you have "
                           "permission to do so).")

    @commands.group(name="nhentai", brief="A command group for commands that connect to nhentai's API.",
                    description="A command group for commands that connect to nhentai's API.")
    async def nhentai(self, ctx):
        if not ctx.invoked_subcommand:
            if ctx.channel.is_nsfw():
                embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
                embed.set_footer(text=self.bot.KAEBOT_VERSION)
                embed.set_author(name="KaeBot", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

                subcommands = ""
                for comm in NSFW.nhentai.commands:
                    subcommands += comm.name
                embed.add_field(name="No command specified.",
                                value=f"Please specify a subcommand: {subcommands}",
                                inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("\U00002757This command cannot execute in a non-NSFW channel.\n"
                               "Try using this command in an NSFW channel (or set this channel to NSFW if you have "
                               "permission to do so).")


def setup(bot):
    bot.add_cog(NSFW(bot))
