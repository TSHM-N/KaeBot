import discord
from discord.ext import commands
import json, asyncio, random, difflib, asyncpg, math
from abc import ABC, abstractmethod

# these classes are made for convenience and scalability
# note that damagecalc is always to calculate outgoing (dealt) damage, not incoming (taken) damage


class Character(ABC):
    @abstractmethod
    async def damagecalc(self, resistance: int):
        pass


class Player(Character):
    def __init__(self, bot, playerrecord: asyncpg.Record):
        self.bot = bot

        self.name = playerrecord["name"]
        self.level = playerrecord["level"]
        self.stats = playerrecord["stats"]  # Note that these will all be str digits; cast to int if using numerically
        self.items = playerrecord["items"]
        self.equipped = playerrecord["equipped"]  # Note that these are str, not Weapon/Armour
        self.exp = playerrecord["exp"]
        self.kaecoins = playerrecord["kaecoins"]

        self.hp = float(self.stats["CON"]) * 2 - (float(self.stats["CON"]) * 0.05)
        self.maxhp = self.hp

    async def damagecalc(self, enemyresistance: int):
        characterstats = self.stats
        weaponobj = await KaeRPG.getweaponobj(self.equipped["weapon"])

        scalingmultiplier = {}
        for key, val in weaponobj.scaling.items():
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
        fluctuation = random.uniform(weaponobj.damage + rawdamageboost * -0.25, weaponobj.damage + rawdamageboost * 0.25)
        finaldamage = round(
            ((weaponobj.damage + rawdamageboost) * (rawdamageboost * 0.1) * critboost + fluctuation) - enemyresistance, 2
        )
        return finaldamage if finaldamage >= 0 else 0

    @staticmethod
    async def calcrequiredexp(self, threshold):  # threshold is typically current level + 1
        return math.log(1.2, threshold) + threshold + 7

    async def levelup(self, ctx):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                currentlevel = await conn.fetchval(
                    "SELECT level FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)
                )
                await conn.execute(
                    "UPDATE kaerpg_characterinfo SET level = $1 WHERE user_id = $2",
                    currentlevel + 1,
                    str(ctx.author.id),
                )
        await ctx.send(f"You levelled up! You are now level {currentlevel + 1}.")

# IMPORTANT NOTE: NONE OF THE BELOW TYPES SHOULD BE CREATED MANUALLY!!!
# THEY ARE ALL GENERATED ON STARTUP AND CATEGORISED INTO KAERPG CLASS ATTRIBUTES
# USE KaeRPG.getitemobj() / KaeRPG.getenemyobj() / KaeRPG.getdungeonobj()


class Enemy(Character):
    def __init__(self, enemyname: str, enemydict: dict):
        self.name = enemyname
        self.hp = enemydict["Health"]
        self.resistance = enemydict["Resistance"]
        self.damage = enemydict["Damage"]
        self.agility = enemydict["Agility"]

        self.maxhp = self.hp

    async def damagecalc(self, playerprotection: int):
        finaldamage = round(
            self.damage + random.uniform(self.damage * 0.2, self.damage * 0.5) - playerprotection / 3, 2
        )
        return finaldamage if finaldamage >= 0 else 0


class Dungeon:
    def __init__(self, dungeonname: str, dungeondict: dict):
        self.name = dungeonname
        self.enemies = dungeondict["Enemies"]
        self.enemycount = dungeondict["Number of Enemies"]
        self.level = dungeondict["Minlevel"]
        self.bosses = dungeondict["Bosses"]


class Item(ABC):
    pass


class Weapon(Item):
    def __init__(self, name, itemdict):
        self.name = name
        self.rank = itemdict["Rank"]
        self.damage = itemdict["Damage"]
        self.scaling = itemdict["Scaling"]
        self.info = itemdict["Info"]


class Armour(Item):
    def __init__(self, name, itemdict):
        self.name = name
        self.rank = itemdict["Rank"]
        self.protection = itemdict["Protection"]
        self.weight = itemdict["Weight"]
        self.info = itemdict["Info"]


class Consumable(Item):
    def __init__(self, name, itemdict):
        self.name = name
        self.value = itemdict["Value"]
        self.effect = itemdict["Effect"]
        self.info = itemdict["Info"]


class KaeRPG:
    def __init__(self, bot):
        self.bot = bot

    with open("cogs/kaerpg/kaerpg_items.json", "r") as f:
        items = []
        weapons = []
        armour = []
        consumables = []
        _rawitems = json.load(f)

        for item in _rawitems["Weapons"]:
            currentweapon = Weapon(item, _rawitems["Weapons"][item])
            items.append(currentweapon)
            weapons.append(currentweapon)

        for item in _rawitems["Armour"]:
            currentarmour = Armour(item, _rawitems["Armour"][item])
            items.append(currentarmour)
            armour.append(currentarmour)

        for item in _rawitems["Consumables"]:
            currentconsumable = Consumable(item, _rawitems["Consumables"][item])
            items.append(currentconsumable)
            consumables.append(currentconsumable)

    with open("cogs/kaerpg/kaerpg_enemies.json", "r") as f:
        dungeons = []
        enemies = []

        _rawitems = json.load(f)
        for dungeon in _rawitems["Dungeons"]:
            dungeons.append(Dungeon(dungeon, _rawitems["Dungeons"][dungeon]))
        for enemy in _rawitems["Enemies"]:
            enemies.append(Enemy(enemy, _rawitems["Enemies"][enemy]))

    @staticmethod
    async def getitemobj(itemname: str):
        return next((x for x in KaeRPG.items if x.name == itemname), None)

    # these are for the sake of specifity

    @staticmethod
    async def getweaponobj(itemname: str):
        return next((x for x in KaeRPG.weapons if x.name == itemname), None)

    @staticmethod
    async def getarmourobj(itemname: str):
        return next((x for x in KaeRPG.armour if x.name == itemname), None)

    @staticmethod
    async def getconsumableobj(itemname: str):
        return next((x for x in KaeRPG.consumables if x.name == itemname), None)

    @staticmethod
    async def getenemyobj(enemyname: str):
        return next((x for x in KaeRPG.enemies if x.name == enemyname), None)

    @staticmethod
    async def getdungeonobj(dungeonname: str):
        return next((x for x in KaeRPG.dungeons if x.name == dungeonname), None)

    async def battlecontroller(self, ctx, player: Player, dungeon: Dungeon):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        actions = ["strike", "guard", "flee", "item"]

        for enemyindex in range(1, dungeon.enemycount + 1):
            enemy = await KaeRPG.getenemyobj(random.choice(dungeon.enemies))
            embed.add_field(name=f"Enemy {enemyindex} of {dungeon.name}:", value=f"{enemy.name}", inline=False)

            # codes: 0: pass, 1: break (player win), -1: return (player fail)
            # these codes are interpreted by the caller of the function
            async def playerturn():
                if action == "strike":
                    turndamagedelivered = await player.damagecalc(enemy.resistance)
                    enemy.hp -= turndamagedelivered
                    if enemy.hp <= 0:
                        await ctx.send(
                            f"\U00002620With a final blow worth {turndamagedelivered:.2f}HP, you kill the {enemy.name}."
                        )
                        return 1
                    else:
                        await ctx.send(
                            f"\U00002694You strike the {enemy.name} for {turndamagedelivered:.2f}HP, leaving it "
                            f"with {enemy.hp:.2f}HP."
                        )
                        return 0
                elif action == "guard":
                    pass
                elif action == "flee":
                    await ctx.send("You fled the dungeon like a coward.")
                    return -1
                elif action == "item":
                    pass

            async def enemyturn():  # should only ever return 0 or -1
                turndamagetaken = await enemy.damagecalc((await KaeRPG.getitemobj(player.equipped["armour"])).protection)
                player.hp -= turndamagetaken
                round(player.hp, 2)
                if player.hp <= 0:
                    await ctx.send(
                        f"\U0001f480The {enemy.name} smites you down with a final blow worth "
                        f"{turndamagetaken:.2f}HP.\nDungeon failed..."
                    )
                    return -1
                else:
                    await ctx.send(
                        f"\U00002694{enemy.name} strikes you for {turndamagetaken:.2f}HP, "
                        f"leaving you with {player.hp:.2f}HP."
                    )
                    return 0

            turn = 1
            while True:
                embed.add_field(
                    name=f"Turn {turn}: You're fighting {enemy.name} ({enemy.hp:.2f}/{enemy.maxhp}HP).",
                    value=f"{player.name}'s health: {player.hp:.2f}/{player.maxhp}HP.\nActions:\n"
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

                if int(player.stats["AGI"]) > enemy.agility:
                    state = await playerturn()
                    if state == 0:  # continue (pass)
                        pass
                    elif state == 1:  # break (next pass)
                        break
                    elif state == -1:  # fail (return)
                        return
                    else:
                        raise NotImplementedError(f"Illegal state {state} (should be 0, 1 or -1)")

                    state = await enemyturn()
                    if state == 0:  # continue (pass)
                        pass
                    elif state == -1:  # fail (return)
                        return
                    else:
                        raise NotImplementedError(f"Illegal state {state} (should be 0 or -1)")
                else:
                    state = await enemyturn()
                    if state == 0:  # continue (pass)
                        pass
                    elif state == -1:  # fail (return)
                        return
                    else:
                        raise NotImplementedError(f"Illegal state {state} (should be 0 or -1)")

                    state = await playerturn()
                    if state == 0:  # continue (pass)
                        pass
                    elif state == 1:  # break (next pass)
                        break
                    elif state == -1:  # fail (return)
                        return
                    else:
                        raise NotImplementedError(f"Illegal state {state} (should be 0, 1 or -1)")
                turn += 1
            rawexp = round((enemy.maxhp + enemy.damage + enemy.resistance) * (1/3))
            gainedexp = rawexp + round(random.uniform(rawexp * -0.25, rawexp * 0.25))
            await ctx.send(f"\U00002747You earned {gainedexp}XP from killing {enemy.name}.")

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
            embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
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
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
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
        name="makecharacter", brief="Create a KaeRPG character.", description="Start KaeRPG by creating a character."
    )
    async def makecharacter(self, ctx):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                if await conn.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)):
                    await ctx.send("You already have a character.")
                else:
                    embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
                    embed.set_footer(text=self.bot.KAEBOT_VERSION)
                    embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

                    await ctx.send(
                        "Entered character creation!\n"
                        "Firstly, specify your character's name (20 characters or less)."
                    )
                    while True:
                        name = await self.bot.wait_for(
                            "message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                        )
                        name = name.content
                        if len(name) <= 20:
                            break
                        else:
                            await ctx.send("That name is too long (>20 characters). Try again.")

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
                            "message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel
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
                    for weapon in ["Lumberer's Axe", "Makeshift Shiv", "Hunter's Bow", "Tattered Scroll"]:
                        weaponobj = await KaeRPG.getitemobj(weapon)
                        startweapons += f"{weaponobj.name}:\n"
                        startweapons += f"Rank: {weaponobj.rank}\n"
                        startweapons += f"Damage: {weaponobj.damage}\n"
                        startweapons += "Scaling: "
                        for stat, scale in weaponobj.scaling.items():
                            startweapons += f"{stat} {scale} / "
                        startweapons = startweapons[:-3] + "\n"
                        startweapons += f"Info: {weaponobj.info}"
                        if not weapon == "Tattered Scroll":
                            startweapons += "\n\n"
                    embed.add_field(name="Starting weapon choices:", value=startweapons, inline=False)

                    await ctx.send(
                        f"Your character is named {name} and has the following stats: {stats}. What weapon will they start with?\n",
                        embed=embed,
                    )
                    embed.clear_fields()
                    while True:
                        weapon = await self.bot.wait_for(
                            "message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                        )
                        weapon = weapon.content
                        if weapon not in ["Lumberer's Axe", "Makeshift Shiv", "Hunter's Bow", "Tattered Scroll"]:
                            await ctx.send("That's not one of the specified starting weapons.")
                        else:
                            break

                    startarmour = ""
                    for armour in ["Leather Carapace", "Warrior's Mail", "Rusted Paladin's Armour"]:
                        armourobj = await KaeRPG.getitemobj(armour)
                        startarmour += f"{armourobj.name}:\n"
                        startarmour += f"Rank: {armourobj.rank}\n"
                        startarmour += f"Protection: {armourobj.protection}\n"
                        startarmour += f"Weight: {armourobj.weight}\n"
                        startarmour += f"Info: {armourobj.info}"
                        if not armour == "Rusted Paladin's Armour":
                            startarmour += "\n\n"
                    embed.add_field(name="Starting armour choices:", value=startarmour, inline=False)

                    await ctx.send(
                        f"Your character is named {name} with the stats {stats} and the weapon {weapon}. "
                        f"What armour will they start with?\n",
                        embed=embed,
                    )
                    embed.clear_fields()
                    while True:
                        armour = await self.bot.wait_for(
                            "message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                        )
                        armour = armour.content
                        if armour not in ["Leather Carapace", "Warrior's Mail", "Rusted Paladin's Armour"]:
                            await ctx.send("That's not one of the specified starting armours.")
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
                if await conn.fetch("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)):
                    await ctx.send("Are you sure you want to delete your character? (y/n)")
                    while True:
                        check = await self.bot.wait_for(
                            "message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                        )
                        check = check.content.lower()
                        if check == "y":
                            await ctx.send("Deleting character from KaeDB...")
                            await conn.execute(
                                "DELETE FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)
                            )
                            return await ctx.send("Character deleted.")
                        elif check == "n":
                            return await ctx.send("Character deletion cancelled.")
                        else:
                            await ctx.send("Specify Y or N as an answer.")
                else:
                    await ctx.send("You don't have a character to delete.")

    @kaerpg.command(name="iteminfo", brief="Check an item.", description="View an item's information.")
    async def iteminfo(self, ctx, *, item: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name=f"KaeRPG: Info for '{item}'", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        itemobj = await KaeRPG.getitemobj(item)
        if itemobj:  # If in item list:
            attributes = list(filter(lambda x: not x.startswith("_") and not x == "name", dir(itemobj)))
            for attr in attributes:
                content = getattr(itemobj, attr)
                if isinstance(content, dict):  # if scaling
                    stringcontent = ""
                    for stat, scale in content.items():
                        stringcontent += f"{stat} {scale} / "
                    embed.add_field(name=attr.capitalize(), value=stringcontent[:-3], inline=True)
                else:
                    embed.add_field(name=attr.capitalize(), value=content, inline=True)
        else:
            names = list(map(lambda x: x.name, KaeRPG.items))
            similaritems = difflib.get_close_matches(item, names, n=5, cutoff=0.6)
            embedcontent = ""
            for similar in similaritems:
                embedcontent += f"{similar}\n"
            embedcontent = embedcontent if embedcontent else "No similar matches found."
            embed.add_field(name="No matches found. Did you mean:", value=embedcontent, inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="characterlist",
        brief="List all characters in KaeRPG.",
        description="List all of the characters registered in KaeRPG.",
    )
    async def characterlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                charlist = await conn.fetch("SELECT * FROM kaerpg_characterinfo")
        embedcontent = ""
        for record in charlist:
            embedcontent += f"{record['name']} | {self.bot.get_user(int(record['user_id'])).display_name} |"
            embedcontent += f" {self.bot.get_user(int(record['user_id'])).id}\n"
        embed.add_field(name="KaeRPG Character List", value=embedcontent, inline=False)
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
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        if user is None:
            user = ctx.author
        embed.set_thumbnail(url=user.avatar_url)

        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                rawinfo = await conn.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(user.id))
        if rawinfo is None:  # No info exists, aka no character
            return await ctx.send("This user doesn't have a KaeRPG character.")

        character = Player(self.bot, rawinfo)
        statstring = ""
        for statname, stat in character.stats.items():
            statstring += f"{statname} {stat} / "
        itemstring = ""
        for item in character.items:
            itemstring += f"{item}, "
        equippedstring = ""
        for item in character.equipped.values():
            equippedstring += f"{item} & "

        embed.add_field(
            name=f"Character Information for {user.display_name}:",
            value=f"Character Name: {character.name}\n"
            f"Level: {character.level}\n"
            f"Current EXP: {character.exp}\n"
            f"Stats: {statstring[:-3]}\n"
            f"Items: {itemstring[:-2]}\n"
            f"Equipped: {equippedstring[:-3]}\n"
            f"KaeCoins: {character.kaecoins}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="dungeonlist", brief="Lists all dungeons in KaeRPG.", description="Lists all dungeons in KaeRPG."
    )
    async def dungeonlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embedcontent = ""
        for dungeon in KaeRPG.dungeons:
            embedcontent += f"{dungeon.name} (minimum level: {dungeon.level}, number of enemies:"
            embedcontent += f" {dungeon.enemycount}, number of bosses: {len(dungeon.bosses)})\n"
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
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        embedcontent = dict.fromkeys(["Omega", "Beta", "Alpha", "S", "A", "B", "C", "D"], "")
        for item in KaeRPG.weapons:
            embedcontent[item.rank] += f"{item.name}, "

        for rank, content in embedcontent.items():
            if content.endswith(", "):
                content = content[:-2]
            content = content if content else "No items of this rank exist."
            embedcontent[rank] = content

        for key, value in embedcontent.items():
            embed.add_field(name=f"{key} Rank:", value=value, inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(
        name="armourlist",
        brief="Lists all armour in KaeRPG.",
        description="Lists all armour in KaeRPG (sorted by rank).",
    )
    async def armourlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        embedcontent = dict.fromkeys(["Omega", "Beta", "Alpha", "S", "A", "B", "C", "D"], "")
        for item in KaeRPG.armour:
            embedcontent[item.rank] += f"{item.name}, "

        for rank, content in embedcontent.items():
            if content.endswith(", "):
                content = content[:-2]
            content = content if content else "No items of this rank exist."
            embedcontent[rank] = content

        for key, value in embedcontent.items():
            embed.add_field(name=f"{key} Rank:", value=value, inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(name="equip", brief="Equip an item.", description="Equip an item from your KaeRPG inventory.")
    async def equip(self, ctx, *, toequip: str):
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                player = await conn.fetchrow(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)
                )
        if player:
            player = Player(self.bot, player)

            if await KaeRPG.getweaponobj(toequip):
                player.equipped["weapon"] = toequip
            elif await KaeRPG.getarmourobj(toequip):
                player.equipped["armour"] = toequip
            else:
                return await ctx.send("That is not a valid, equippable item. Are you sure it is in your inventory?")

            async with self.bot.kaedb.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE kaerpg_characterinfo SET equipped = $1 WHERE user_id = $2",
                        player.equipped,
                        str(ctx.author.id),
                    )
            await ctx.send(f"Equipped {toequip}.")

        else:
            await ctx.send("You don't have a character. Use 'prefix kaerpg makecharacter' to make one.")

    @kaerpg.command(name="raid", brief="Raid a dungeon!", description="Raid a dungeon!")
    async def raid(self, ctx, *, dungeonstr: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                playerrecord = await conn.fetchrow(
                    "SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)
                )
                if playerrecord:
                    playerobj = Player(self.bot, playerrecord)
                else:
                    return await ctx.send("You don't have a character to raid this dungeon with! Use 'prefix kaerpg makecharacter'.")

                dungeonobj = await KaeRPG.getdungeonobj(dungeonstr)
                if not dungeonobj:
                    return await ctx.send("That is not a KaeRPG dungeon. Type 'prefix kr dungeonlist' to find dungeons.")

                if dungeonobj.level > playerobj.level:
                    return await ctx.send(f"Your level is too low for this dungeon (required level: {dungeonobj.level}).")

                embed.add_field(name=f"Starting a Raid on {dungeonstr}!", value="Raid starting in 5 seconds...", inline=False)
                await ctx.send(embed=embed)
                embed.clear_fields()
                await asyncio.sleep(5)

                await KaeRPG.battlecontroller(self, ctx, playerobj, dungeonobj)


def setup(bot):
    bot.add_cog(KaeRPG(bot))
