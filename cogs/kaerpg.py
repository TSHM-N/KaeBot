import discord
from discord.ext import commands
import json, asyncio, random, difflib


class KaeRPG:
    def __init__(self, bot):
        self.bot = bot

    with open("cogs/kaerpg/kaerpg_items.json", "r") as f:
        items = json.load(f)

    with open("cogs/kaerpg/kaerpg_enemies.json", "r") as f:
        dungeons = json.load(f)["Dungeons"]
        f.seek(0)
        enemies = json.load(f)["Enemies"]

    @staticmethod
    async def playerdamagecalc(
        self,
        weapondamage: int,
        weaponscaling: dict,
        characterstats: dict,
        enemyresistance: int,
    ):
        scalingmultiplier = {}
        for key, val in weaponscaling.items():
            if val == "A":
                scalingmultiplier[key] = 0.10
            elif val == "B":
                scalingmultiplier[key] = 0.08
            elif val == "C":
                scalingmultiplier[key] = 0.06
            elif val == "D":
                scalingmultiplier[key] = 0.04
            elif val == "N/A":
                scalingmultiplier[key] = 0
            else:
                raise ValueError(f"Bad scaling value in keypair {key}:{val}")

        rawdamageboost = 0
        for key, val in scalingmultiplier.items():
            rawdamageboost += val * int(characterstats[key])

        critboost = 1.5 if random.random() > 0.95 else 1
        fluctuation = random.uniform(
            weapondamage + rawdamageboost * -0.25, weapondamage + rawdamageboost * 0.25
        )
        finaldamage = round(
            (
                (weapondamage + rawdamageboost) * (rawdamageboost * 0.1) * critboost
                + fluctuation
            )
            - enemyresistance,
            2,
        )
        return finaldamage if finaldamage >= 0 else 0

    @staticmethod
    async def enemydamagecalc(self, enemydamage: int, playerprotection: int):
        finaldamage = round(
            enemydamage
            + random.uniform(enemydamage * 0.2, enemydamage * 0.5)
            - playerprotection / 3,
            2,
        )
        return finaldamage if finaldamage >= 0 else 0

    @staticmethod
    async def levelup(self, ctx):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                currentlevel = await conn.fetchval(
                    "SELECT level FROM kaerpg_characterinfo WHERE user_id = $1",
                    str(ctx.author.id),
                )
                await conn.execute(
                    "UPDATE kaerpg_characterinfo SET level = $1 WHERE user_id = $2",
                    currentlevel + 1,
                    str(ctx.author.id),
                )
        await ctx.send(f"You levelled up! You are now level {currentlevel + 1}.")

    @staticmethod
    async def battlecontroller(self, ctx, player: dict, dungeon: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )
        actions = ["strike", "guard", "flee", "item"]
        usable = []
        for item in player["items"]:
            if item in KaeRPG.items["Consumables"]:
                usable.append(item)
        playerhp = float(player["stats"]["CON"]) * 2 - (
            float(player["stats"]["CON"]) * 0.05
        )
        playermaxhp = playerhp

        for enemyindex in range(1, KaeRPG.dungeons[dungeon]["Number of Enemies"] + 1):
            enemy = random.choice(KaeRPG.dungeons[dungeon]["Enemies"])
            enemyhp = KaeRPG.enemies[enemy]["Health"]
            enemymaxhp = enemyhp
            turn = 1
            embed.add_field(
                name=f"Enemy {enemyindex} of {dungeon}:", value=f"{enemy}", inline=False
            )

            while True:
                embed.add_field(
                    name=f"Turn {turn}: You're fighting {enemy} ({enemyhp}/{enemymaxhp}HP).",
                    value=f"{player['name']}'s health: {playerhp:.2f}/{playermaxhp}HP.\nActions:\n"
                    f"Strike, Guard, Flee, Item",
                    inline=False,
                )
                await ctx.send(embed=embed)
                embed.clear_fields()

                action = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author
                    and m.channel == ctx.channel
                    and m.content.lower() in actions,
                )
                action = action.content.lower()
                assert action in actions

                if int(player["stats"]["AGI"]) > KaeRPG.enemies[enemy]["Agility"]:
                    if action == "strike":
                        turndamagedelivered = await KaeRPG.playerdamagecalc(
                            self,
                            KaeRPG.items["Weapons"][player["equipped"]["weapon"]][
                                "Damage"
                            ],
                            KaeRPG.items["Weapons"][player["equipped"]["weapon"]][
                                "Scaling"
                            ],
                            player["stats"],
                            KaeRPG.enemies[enemy]["Resistance"],
                        )
                        enemyhp -= turndamagedelivered
                        if enemyhp <= 0:
                            await ctx.send(
                                f"With a final blow worth {turndamagedelivered:.2f}HP, you deliver "
                                f"the final blow to the {enemy}."
                            )
                            break
                        else:
                            await ctx.send(
                                f"You strike the {enemy} for {turndamagedelivered:.2f}HP, leaving it "
                                f"with {enemyhp}HP."
                            )
                    elif action == "guard":
                        pass
                    elif action == "flee":
                        return await ctx.send("You fled the dungeon like a coward.")
                    elif action == "item":
                        pass

                    turndamagetaken = await KaeRPG.enemydamagecalc(
                        self,
                        KaeRPG.enemies[enemy]["Damage"],
                        KaeRPG.items["Armour"][player["equipped"]["armour"]][
                            "Protection"
                        ],
                    )
                    playerhp -= turndamagetaken
                    round(playerhp, 2)
                    if playerhp <= 0:
                        return await ctx.send(
                            f"The {enemy} smites you dead with a final blow worth "
                            f"{turndamagetaken:.2f}HP.\nDungeon failed..."
                        )
                    else:
                        await ctx.send(
                            f"{enemy} strikes you for {turndamagetaken:.2f}HP, leaving you with {playerhp:.2f}HP."
                        )

                else:
                    turndamagetaken = await KaeRPG.enemydamagecalc(
                        self,
                        KaeRPG.enemies[enemy]["Damage"],
                        KaeRPG.items["Armour"][player["equipped"]["armour"]][
                            "Protection"
                        ],
                    )
                    playerhp -= turndamagetaken
                    round(playerhp, 2)
                    if playerhp <= 0:
                        return await ctx.send(
                            f"The {enemy} smites you dead with a final blow worth "
                            f"{turndamagetaken:.2f}HP.\nDungeon failed..."
                        )
                    else:
                        await ctx.send(
                            f"{enemy} strikes you for {turndamagetaken:.2f}HP, leaving you with {playerhp:.2f}HP."
                        )

                    if action == "strike":
                        turndamagedelivered = await KaeRPG.playerdamagecalc(
                            self,
                            KaeRPG.items["Weapons"][player["equipped"]["weapon"]][
                                "Damage"
                            ],
                            KaeRPG.items["Weapons"][player["equipped"]["weapon"]][
                                "Scaling"
                            ],
                            player["stats"],
                            KaeRPG.enemies[enemy]["Resistance"],
                        )
                        enemyhp -= turndamagedelivered
                        if enemyhp <= 0:
                            await ctx.send(
                                f"With a final blow worth {turndamagedelivered}HP, you deliver "
                                f"the final blow to the {enemy}."
                            )
                            break
                        else:
                            await ctx.send(
                                f"You strike the {enemy} for {turndamagedelivered}HP, leaving it"
                                f"with {enemyhp}HP."
                            )
                    elif action == "guard":
                        pass
                    elif action == "flee":
                        return await ctx.send("You fled the dungeon like a coward.")
                    elif action == "item":
                        pass

                turn += 1
            experience = int(
                KaeRPG.enemies[enemy]["Health"]
                + KaeRPG.enemies[enemy]["Damage"]
                + KaeRPG.enemies[enemy]["Resistance"] / 3
            )
            await ctx.send(f"You earned {experience}XP from killing {enemy}.")

    @commands.group(
        name="kaerpg",
        brief="A command group for every KaeRPG command. Aliased to kr.",
        description="A command group for every KaeRPG command. Aliased to kr.",
        aliases=["kr"],
    )
    async def kaerpg(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
            embed.set_footer(text=self.bot.KAEBOT_VERSION)
            embed.set_author(
                name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
            )
            embedcontent = ""
            for command in KaeRPG.kaerpg.commands:
                embedcontent += f"{command}\n"
            embed.add_field(name="KaeRPG commands:", value=embedcontent, inline=False)
            await ctx.send(embed=embed)

    @kaerpg.command(
        name="beginnersguide",
        brief="Open a beginner's guide for KaeRPG.",
        description="Open a beginner's guide for KaeRPG.",
    )
    async def beginnersguide(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )
        embed.add_field(
            name="Beginner's Guide to KaeRPG",
            value="To start playing, create a character using 'prefix kaerpg makecharacter'.\n"
            "Once you have a character, you can access information related to your character using"
            " 'prefix kaerpg characterinfo'. This includes your character name, level, experience and "
            "inventory.\nTo access a dungeon and fight enemies for loot, type 'prefix kaerpg dungeonlist'"
            " to list dungeons and type 'prefix kaerpg raid dungeonname' to raid that dungeon.\n"
            "For more information, type 'prefix kaerpg info' and then type 'prefix kaerpg info topic'"
            " to learn about a specific topic.\n"
            "For a list of other commands, type 'prefix kaerpg'.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="makecharacter",
        brief="Create a KaeRPG character.",
        description="Start KaeRPG by creating a character.",
    )
    async def makecharacter(self, ctx):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                if await conn.fetchrow(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1",
                    str(ctx.author.id),
                ):
                    await ctx.send("You already have a character.")
                else:
                    embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
                    embed.set_footer(text=self.bot.KAEBOT_VERSION)
                    embed.set_author(
                        name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
                    )

                    await ctx.send(
                        "Entered character creation!\n"
                        "Firstly, specify your character's name (20 characters or less)."
                    )
                    while True:
                        name = await self.bot.wait_for(
                            "message",
                            check=lambda m: m.author == ctx.author
                            and m.channel == ctx.channel,
                        )
                        name = name.content
                        if len(name) <= 20:
                            break
                        else:
                            await ctx.send(
                                "That name is too long (>20 characters). Try again."
                            )

                    statspecs = {
                        "1": "STR 14 / DEX 12 / PRE 10 / ARC 8 / CON 13 / AGI 8",
                        "2": "STR 8 / DEX 16 / PRE 11 / ARC 8 / CON 10 / AGI 12",
                        "3": "STR 10 / DEX 12 / PRE 16 / ARC 10 / CON 8 / AGI 9",
                        "4": "STR 21 / DEX 10 / PRE 8 / ARC 9 / CON 8 / AGI 9",
                        "5": "STR 8 / DEX 9 / PRE 12 / ARC 16 / CON 8 / AGI 12",
                    }
                    for key in statspecs.keys():
                        embed.add_field(name=key, value=statspecs[key], inline=False)
                    await ctx.send(
                        f"Your character is named {name}. What stats will they have? (Choose 1, 2, 3, 4 or 5).",
                        embed=embed,
                    )
                    embed.clear_fields()

                    while True:
                        statchoice = await self.bot.wait_for(
                            "message",
                            check=lambda m: m.author == ctx.author
                            and m.channel == ctx.channel,
                        )
                        statchoice = statchoice.content
                        if statchoice not in ["1", "2", "3", "4", "5"]:
                            await ctx.send(
                                "That's not one of the stat specs previously sent. Make sure to phrase your answer "
                                "as '1', not 'Stat Spec 1' (no quotes)."
                            )
                        else:
                            stats = statspecs[statchoice]
                            break

                    startweapons = ""
                    for weapon in [
                        "Lumber's Axe",
                        "Makeshift Shiv",
                        "Hunter's Bow",
                        "Tattered Scroll",
                    ]:
                        startweapons += f"{weapon}:\n"
                        startweapons += (
                            f"Rank: {KaeRPG.items['Weapons'][weapon]['Rank']}\n"
                        )
                        startweapons += (
                            f"Damage: {KaeRPG.items['Weapons'][weapon]['Damage']}\n"
                        )
                        startweapons += "Scaling: "
                        for stat, scale in KaeRPG.items["Weapons"][weapon][
                            "Scaling"
                        ].items():
                            startweapons += f"{stat} {scale} / "
                        startweapons = startweapons[:-3] + "\n"
                        startweapons += (
                            f"Info: {KaeRPG.items['Weapons'][weapon]['Info']}"
                        )
                        if not weapon == "Tattered Scroll":
                            startweapons += "\n\n"
                    embed.add_field(
                        name="Starting weapon choices:",
                        value=startweapons,
                        inline=False,
                    )

                    await ctx.send(
                        f"Your character is named {name} and has the following stats: {stats}. What weapon will they start with?\n",
                        embed=embed,
                    )
                    embed.clear_fields()
                    while True:
                        weapon = await self.bot.wait_for(
                            "message",
                            check=lambda m: m.author == ctx.author
                            and m.channel == ctx.channel,
                        )
                        weapon = weapon.content
                        if weapon not in [
                            "Lumber's Axe",
                            "Makeshift Shiv",
                            "Hunter's Bow",
                            "Tattered Scroll",
                        ]:
                            await ctx.send(
                                "That's not one of the specified starting weapons."
                            )
                        else:
                            break

                    startarmour = ""
                    for armour in [
                        "Leather Carapace",
                        "Warrior's Mail",
                        "Rusted Paladin's Armour",
                    ]:
                        startarmour += f"{armour}:\n"
                        startarmour += (
                            f"Rank: {KaeRPG.items['Armour'][armour]['Rank']}\n"
                        )
                        startarmour += f"Protection: {KaeRPG.items['Armour'][armour]['Protection']}\n"
                        startarmour += (
                            f"Type: {KaeRPG.items['Armour'][armour]['Type']}\n"
                        )
                        startarmour += f"Info: {KaeRPG.items['Armour'][armour]['Info']}"
                        if not armour == "Rusted Paladin's Armour":
                            startarmour += "\n\n"
                    embed.add_field(
                        name="Starting armour choices:", value=startarmour, inline=False
                    )

                    await ctx.send(
                        f"Your character is named {name} with the stats {stats} and the weapon {weapon}. What armour will they start with?\n",
                        embed=embed,
                    )
                    embed.clear_fields()
                    while True:
                        armour = await self.bot.wait_for(
                            "message",
                            check=lambda m: m.author == ctx.author
                            and m.channel == ctx.channel,
                        )
                        armour = armour.content
                        if armour not in [
                            "Leather Carapace",
                            "Warrior's Mail",
                            "Rusted Paladin's Armour",
                        ]:
                            await ctx.send(
                                "That's not one of the specified starting armours."
                            )
                        else:
                            break

                    embed.add_field(
                        name="Your character was added to KaeRPG!",
                        value=f"{name} was just added to KaeRPG with the following stats:\n"
                        f"{stats}\n"
                        f"...and the following items:\n"
                        f"{weapon}, {armour}\n"
                        "You can now play KaeRPG. Use 'kaerpg beginnersguide' to learn how to play.",
                        inline=False,
                    )

                    statdict = {}
                    stats = stats.split(" / ")
                    for stat in stats:
                        dlist = stat.split(" ")
                        statdict[dlist[0]] = dlist[1]
                    await conn.execute(
                        "INSERT INTO kaerpg_characterinfo VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                        str(ctx.author.id),
                        name,
                        1,
                        0,
                        statdict,
                        [weapon, armour],
                        0,
                        {"armour": armour, "weapon": weapon},
                    )
                    await ctx.send(embed=embed)

    @kaerpg.command(
        name="delcharacter",
        brief="Delete your KaeRPG character.",
        description="Delete your KaeRPG character permanently.",
    )
    async def delcharacter(self, ctx):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                if await conn.fetch(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1",
                    str(ctx.author.id),
                ):
                    await ctx.send(
                        "Are you sure you want to delete your character? (y/n)"
                    )
                    while True:
                        check = await self.bot.wait_for(
                            "message",
                            check=lambda m: m.author == ctx.author
                            and m.channel == ctx.channel,
                        )
                        check = check.content.lower()
                        if check == "y":
                            await ctx.send("Deleting character from KaeDB...")
                            await conn.execute(
                                "DELETE FROM kaerpg_characterinfo WHERE user_id = $1",
                                str(ctx.author.id),
                            )
                            return await ctx.send("Character deleted.")
                        elif check == "n":
                            return await ctx.send("Character deletion cancelled.")
                        else:
                            await ctx.send("Specify Y or N as an answer.")
                else:
                    await ctx.send("You don't have a character to delete.")

    @kaerpg.command(
        name="iteminfo",
        brief="Check an item.",
        description="View an item's information.",
    )
    async def iteminfo(self, ctx, *, item: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )

        if item in KaeRPG.items["Weapons"].keys():  # If in weapon list:
            itemdict = KaeRPG.items["Weapons"][item]
            embedcontent = f"Rank: {itemdict['Rank']}\n"
            embedcontent += f"Damage: {itemdict['Damage']}\n"
            embedcontent += "Scaling: "
            for scale in itemdict["Scaling"]:
                if scale == "ARC":
                    embedcontent += f"{scale} {itemdict['Scaling'][scale]}"
                else:
                    embedcontent += f"{scale} {itemdict['Scaling'][scale]} / "
            embedcontent += f"\nInfo: *{itemdict['Info']}*"

            embed.add_field(name=item, value=embedcontent, inline=False)
            await ctx.send(embed=embed)

        elif item in KaeRPG.items["Armour"].keys():  # If in armour list:
            itemdict = KaeRPG.items["Armour"][item]
            embedcontent = f"Rank: {itemdict['Rank']}\n"
            embedcontent += f"Protection: {itemdict['Protection']}\n"
            embedcontent += f"Type: {itemdict['Type']}\n"
            embedcontent += f"Info: *{itemdict['Info']}*"

            embed.add_field(name=item, value=embedcontent, inline=False)
            await ctx.send(embed=embed)

        elif item in KaeRPG.items["Consumables"]:  # If in consumables list:
            itemdict = KaeRPG.items["Consumables"][item]
            embedcontent = f"Value: {itemdict['Value']}\n"
            embedcontent += f"Effect: {itemdict['Effect']}\n"
            embedcontent += f"Info: *{itemdict['Info']}*"

            embed.add_field(name=item, value=embedcontent, inline=False)
            await ctx.send(embed=embed)

        else:
            similaritems = difflib.get_close_matches(
                item, KaeRPG.items["Weapons"].keys(), n=5, cutoff=0.6
            )
            embedcontent = ""
            for similar in similaritems:
                embedcontent += f"{similar}\n"
            embedcontent = embedcontent if embedcontent else "No similar matches found."
            embed.add_field(
                name="No matches found. Did you mean:", value=embedcontent, inline=False
            )
            await ctx.send(embed=embed)

    @kaerpg.command(
        name="characterlist",
        brief="List all characters in KaeRPG.",
        description="List all of the characters registered in KaeRPG.",
    )
    async def characterlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )

        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                charlist = await conn.fetch("SELECT * FROM kaerpg_characterinfo")
        embedcontent = ""
        for record in charlist:
            embedcontent += f"{record['name']} | {self.bot.get_user(int(record['user_id'])).display_name} |"
            embedcontent += f" {self.bot.get_user(int(record['user_id'])).id}\n"
        embed.add_field(name="Character List", value=embedcontent, inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="characterinfo",
        brief="Get the character info of a user's character. Aliased to inventory.",
        description="Get character info of your or someone else's character. If a user is not"
        " specified, this command defaults to your character. Aliased to inventory.",
        aliases=["inventory"],
    )
    async def characterinfo(self, ctx, user: commands.MemberConverter = None):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)

        if user is None:
            user = ctx.author
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                rawinfo = await conn.fetchrow(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1",
                    str(user.id),
                )
        if rawinfo is None:  # No info exists, aka no character
            return await ctx.send("This user doesn't have a KaeRPG character.")

        stats = ""
        for key, val in rawinfo["stats"].items():
            stats += f"{key} {val} / "
        stats = stats[:-3]
        items = ""
        for item in rawinfo["items"]:
            items += f"{item}, "
        items = items[:-2]
        kaecoins = rawinfo["kaecoins"]
        equipped = ""
        for equipment in rawinfo["equipped"].values():
            equipped += f"{equipment}, "
        equipped = equipped[:-2]

        embed.add_field(
            name=f"Character Information for {user.display_name}:",
            value=f"Character Name: {rawinfo['name']}\n"
            f"Level: {rawinfo['level']}\n"
            f"Current EXP: {rawinfo['exp']}\n"
            f"Stats: {stats}\n"
            f"Items: {items}\n"
            f"Equipped: {equipped}\n"
            f"KaeCoins: {kaecoins}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="dungeonlist",
        brief="Lists all dungeons in KaeRPG.",
        description="Lists all dungeons in KaeRPG.",
    )
    async def dungeonlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )
        embedcontent = ""
        for dungeon in KaeRPG.dungeons:
            embedcontent += f"{dungeon} (minimum level: {KaeRPG.dungeons[dungeon]['Minlevel']}, number of enemies:"
            embedcontent += f" {KaeRPG.dungeons[dungeon]['Number of Enemies']}, number of bosses: {len(KaeRPG.dungeons[dungeon]['Bosses'])})\n"
        embed.add_field(name="Dungeon List:", value=embedcontent, inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="weaponlist",
        brief="Lists all weapons in KaeRPG.",
        description="Lists all weapons in KaeRPG (sorted by rank).",
    )
    async def weaponlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )

        embedcontent = dict.fromkeys(
            ["Omega", "Beta", "Alpha", "S", "A", "B", "C", "D"], ""
        )
        for item in KaeRPG.items["Weapons"]:
            embedcontent[KaeRPG.items["Weapons"][item]["Rank"]] += f"{item}, "

        for rank, content in embedcontent.items():
            if content.endswith(", "):
                content = content[:-2]
            content = content if content else "No items of this rank exist."
            embedcontent[rank] = content

        embed.add_field(name="Omega Rank:", value=embedcontent["Omega"], inline=False)
        embed.add_field(name="Beta Rank:", value=embedcontent["Beta"], inline=False)
        embed.add_field(name="Alpha Rank:", value=embedcontent["Alpha"], inline=False)
        embed.add_field(name="S Rank:", value=embedcontent["S"], inline=False)
        embed.add_field(name="A Rank:", value=embedcontent["A"], inline=False)
        embed.add_field(name="B Rank:", value=embedcontent["B"], inline=False)
        embed.add_field(name="C Rank:", value=embedcontent["C"], inline=False)
        embed.add_field(name="D Rank:", value=embedcontent["D"], inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="armourlist",
        brief="Lists all armour in KaeRPG.",
        description="Lists all armour in KaeRPG (sorted by rank).",
    )
    async def armourlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )

        embedcontent = dict.fromkeys(
            ["Omega", "Beta", "Alpha", "S", "A", "B", "C", "D"], ""
        )
        for item in KaeRPG.items["Armour"]:
            embedcontent[KaeRPG.items["Armour"][item]["Rank"]] += f"{item}, "

        for rank, content in embedcontent.items():
            if content.endswith(", "):
                content = content[:-2]
            content = content if content else "No items of this rank exist."
            embedcontent[rank] = content

        for key in embedcontent.keys():
            embed.add_field(name=f"{key} Rank:", value=embedcontent[key], inline=False)

        await ctx.send(embed=embed)

    @kaerpg.command(
        name="equip",
        brief="Equip an item.",
        description="Equip an item from your KaeRPG inventory.",
    )
    async def equip(self, ctx, *, toequip: str):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                player = await conn.fetchrow(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1",
                    str(ctx.author.id),
                )
        if player:
            equipment = player["equipped"]
            equipment = equipment if equipment else {}

            equippableweapons = []
            equippablearmour = []
            for item in player["items"]:
                if item in KaeRPG.items["Weapons"]:
                    equippableweapons.append(item)
                elif item in KaeRPG.items["Armour"]:
                    equippablearmour.append(item)

            if toequip in equippableweapons:
                equipment["weapon"] = toequip
            elif toequip in equippablearmour:
                equipment["armour"] = toequip
            else:
                return await ctx.send(
                    "That is not a valid, equippable item (is it in your inventory)?"
                )

            async with self.bot.kaedb.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE kaerpg_characterinfo SET equipped = ($1) WHERE user_id = $2",
                        equipment,
                        str(ctx.author.id),
                    )
            await ctx.send(f"Equipped {toequip}.")

        else:
            await ctx.send(
                "You don't have a character. Use 'prefix kaerpg makecharacter' to make one."
            )

    @kaerpg.command(name="raid", brief="Raid a dungeon!", description="Raid a dungeon!")
    async def raid(self, ctx, *, dungeon: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(
            name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png"
        )

        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                player = await conn.fetchrow(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1",
                    str(ctx.author.id),
                )
                if player:
                    try:  # Test this dungeon exists
                        KaeRPG.dungeons[dungeon]
                    except KeyError:
                        return await ctx.send("That's not a KaeRPG dungeon.")
                    if (
                        KaeRPG.dungeons[dungeon]["Minlevel"]
                        > (
                            await conn.fetchrow(
                                "SELECT level FROM kaerpg_characterinfo WHERE user_id = $1",
                                str(ctx.author.id),
                            )
                        )["level"]
                    ):
                        return await ctx.send(
                            f"Your level is too low for this dungeon (required level: {KaeRPG.dungeons[dungeon]['Minlevel']})."
                        )
                    embed.add_field(
                        name=f"Starting a Raid on {dungeon}!",
                        value="Raid starting in 5 seconds...",
                        inline=False,
                    )
                    await ctx.send(embed=embed)
                    embed.clear_fields()
                    await asyncio.sleep(5)
                    await KaeRPG.battlecontroller(self, ctx, player, dungeon)

                else:
                    await ctx.send(
                        "You don't have a character to raid this dungeon with! Use 'prefix kaerpg makecharacter'."
                    )


def setup(bot):
    bot.add_cog(KaeRPG(bot))
