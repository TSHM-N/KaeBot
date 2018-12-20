import discord
from discord.ext import commands
import aiohttp, bs4


class Genius:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="lyrics",
        brief="Get the lyrics to a song.",
        description="Searches genius.com for the lyrics to a specified song.",
    )
    async def lyrics(self, ctx, *, searchterms):
        baseurl = "https://api.genius.com"
        header = {"Authorization": "Bearer " + self.bot.GENIUS_CLIENTTOKEN}

        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.add_field(
            name=f"Now searching for '{searchterms}' on Genius.com...", value="Searching for lyrics...", inline=False
        )
        await ctx.send(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(baseurl + "/search", headers=header, data={"q": searchterms}) as response:
                resultjson = await response.json()

            async with session.get(
                baseurl + resultjson["response"]["hits"][0]["result"]["api_path"], headers=header
            ) as response:
                songjson = await response.json()

            songurl = songjson["response"]["song"]["url"]
            songtitle = songjson["response"]["song"]["title"]
            songartist = songjson["response"]["song"]["album"]["artist"]["name"]
            songthumbnail = songjson["response"]["song"]["song_art_image_thumbnail_url"]

            async with session.get(songurl) as response:
                responsetext = await response.read()

        lyricsoup = bs4.BeautifulSoup(responsetext, "lxml")
        lyrics = lyricsoup.find("div", class_="lyrics").get_text()
        try:
            embed.set_thumbnail(url=songthumbnail)
        except AttributeError:  # No album art
            pass

        try:
            if len(lyrics) <= 1000:
                embed.add_field(name=f"Lyrics for '{songtitle}' by '{songartist}':", value=lyrics, inline=False)
                await ctx.send(embed=embed)
            else:
                for i in range(0, len(lyrics), 1000):
                    embed.clear_fields()
                    embedcontent = lyrics[i : i + 1000]
                    if not i == list(reversed(range(0, len(lyrics), 1000)))[-0]:
                        embedcontent += "..."
                    if not i == list(range(0, len(lyrics), 1000))[0]:
                        embedcontent = "..." + embedcontent
                    embed.add_field(
                        name=f"Lyrics for '{songtitle}' by '{songartist}':", value=embedcontent, inline=False
                    )
                    await ctx.send(embed=embed)

        except AttributeError:  # No lyrics, artist, title, song etc.
            embed.add_field(
                name="Something went wrong...", value="Oops, something broke. Try another song.", inline=False
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Genius(bot))
