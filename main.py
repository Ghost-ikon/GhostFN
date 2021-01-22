try:
    from typing import Any, Union, Optional

    import asyncio
    import datetime
    import json
    import functools
    import random as py_random
    import subprocess
    import os
    import uvloop
    import sys
    import time

    from fortnitepy.ext import commands

    import aioconsole
    import crayons
    import fortnitepy
    import FortniteAPIAsync
    import sanic
    import aiohttp
except ModuleNotFoundError:
    print(f'[!] Error found, run: install.bat')


sanic_app = sanic.Sanic(__name__) 
server = None

name = ""

filename = 'device.json'

@sanic_app.route('/', methods=['GET'])
async def accept_ping(request: sanic.request.Request):
    return sanic.response.json({"bot": "online"})


@sanic_app.route('/name', methods=['GET'])
async def accept_ping(request: sanic.request.Request):
    return sanic.response.json({"display_name": name})

def get_device_auth_details():
    if os.path.isfile(filename):
        with open(filename, 'r') as fp:
            return json.load(fp)
    return {}

def store_device_auth_details(email, details):
    existing = get_device_auth_details()
    existing[email] = details

    with open(filename, 'w') as fp:
        json.dump(existing, fp)

async def get_authorization_code():
    while True:
        response = await aioconsole.ainput("http://bit.ly/38URYTD "+ " \nGhostFN for an easy lobby bot! Join here if you need help or found any bugs\n https://discord.gg/8AHPRyEzmF \nPut the code and press invio: ")
        if "redirectUrl" in response:
            response = json.loads(response)
            if "?code" not in response["redirectUrl"]:
                print("[!] ERROR: Invalid Response.")
                continue
            code = response["redirectUrl"].split("?code=")[1]
            return code
        else:
            if "https://accounts.epicgames.com/fnauth" in response:
                if "?code" not in response:
                    print("[!] ERROR: Invalid Response.")
                    continue
                code = response.split("?code=")[1]
                return code
            else:
                code = response
                return code

async def event_device_auth_generate(self, details, email):
    print(details)
    with open("auths.json", "r") as f:
        text = f.read()

        auths = json.loads(text)

    auths[email] = details

    with open("auths.json", "w+") as f:
        text = json.dumps(auths)
        f.write(text)

    print('Generated DeviceAuth')

class EasyBot(commands.Bot):
    def __init__(self, email : str, password : str, **kwargs):
        self.status = '🔥 Made with GhostFN 🔥'
        self.kairos = 'CID_017_Athena_Commando_M'
        device_auth_details = get_device_auth_details().get(email, {})
        super().__init__(
            command_prefix='!',
            auth=fortnitepy.AdvancedAuth(
                email=email,
                password=password,
                prompt_authorization_code=False,
                delete_existing_device_auths=True,
                authorization_code=get_authorization_code,
                **device_auth_details
            ),

            status=self.status,
            platform=fortnitepy.Platform(os.getenv("PLATFORM")),

            avatar=fortnitepy.Avatar(
                asset=self.kairos,
                background_colors=fortnitepy.KairosBackgroundColorPreset.PINK.value
            ),


            **kwargs
        )

        self.fortnite_api = FortniteAPIAsync.APIClient()
        self.loop = asyncio.get_event_loop()

        self.default_skin = os.getenv("SKIN")
        self.default_backpack = os.getenv("BACKPACK")
        self.default_pickaxe = os.getenv("PICKAXE")
        self.banner = os.getenv("BANNER")
        self.banner_colour = os.getenv("BANNERCOLOR")
        self.default_level = os.getenv("LEVEL")
        self.default_bp_tier = os.getenv("TIER")
        self.default_emote = os.getenv("EMOTE")

        self.sanic_app = sanic_app
        self.server = server

        self.welcome_message = "Welcome user, \n to get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!"
      #--------------------------  

    async def event_party_invite(self, invite: fortnitepy.ReceivedPartyInvitation):
        await invite.decline()
        print(f'[>] declined: {invite.sender.display_name}.')

    async def event_friend_request(self, request: fortnitepy.IncomingPendingFriend):
        print(f"[>] Received friend request from: [{request.display_name}].")

        await request.accept()
        print(f"[+] New Friend: [{request.display_name}].")

    async def event_party_member_join(self, member: fortnitepy.PartyMember):
        await self.party.send(self.welcome_message.replace('{DISPLAY_NAME}', member.display_name))

        if self.default_party_member_config.cls is not fortnitepy.party.JustChattingClientPartyMember:
            await self.party.me.edit(
                functools.partial(
                    self.party.me.set_outfit,
                    self.default_skin
                ),
                functools.partial(
                    self.party.me.set_backpack,
                    self.default_backpack
                ),
                functools.partial(
                    self.party.me.set_pickaxe,
                    self.default_pickaxe
                ),
                functools.partial(
                    self.party.me.set_banner,
                    icon=self.banner,
                    color=self.banner_colour,
                    season_level=self.default_level
                ),
                functools.partial(
                    self.party.me.set_battlepass_info,
                    has_purchased=True,
                    level=self.default_bp_tier
                )
            )

        

        if self.default_party_member_config.cls is not fortnitepy.party.JustChattingClientPartyMember:
            await self.party.me.clear_emote()
            await self.party.me.set_emote(asset=self.default_emote)

            if self.user.display_name != member.display_name:  # Welcomes the member who just joined.

                await self.party.send(f"Welcome, [{member.display_name}], \n to get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!")
            
                print(f"[+] [{member.display_name}] Joined the Lobby.")



    async def event_command_error(self, ctx: fortnitepy.ext.commands.Context,
                                  error: fortnitepy.ext.commands.CommandError):
        if isinstance(error, fortnitepy.ext.commands.errors.CommandNotFound):
            if isinstance(ctx.message, fortnitepy.FriendMessage):
                await ctx.send('Invalid Command!\n You can try reversing the uppercase letters.')
            else:
                pass
        elif isinstance(error, fortnitepy.ext.commands.errors.MissingRequiredArgument):
            await ctx.send('Error, I need permissions :)')
        elif isinstance(error, fortnitepy.ext.commands.errors.PrivateMessageOnly):
            pass
        else:
            raise error

   #-----------------------------------------
    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Clears the currently set backpack.",
        help="Clears the currently set backpack.\n"
             "Example: !nobackpack"
    )
    async def noback(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.clear_backpack()
        await ctx.send('Backpack set to none.')

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to Golden Peely "
                    "(shortcut for !enlightened CID_701_Athena_Commando_M_BananaAgent 2 350).",
        help="Sets the outfit of the client to Golden Peely.\n"
             "Example: !goldenpeely"
    )
    async def goldenmidas(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.set_outfit(
            asset='CID_694_Athena_Commando_M_CatBurglar',
            variants=self.party.me.create_variants(progressive=4),
            enlightenment=(2, 350)
        )

        await ctx.send(f'Skin set to Golden Peely.')  

    @commands.dm_only()
    @commands.command(
        description="[Party] Sends the defined user a friend request.",
        help="Sends the defined user a friend request.\n"
             "Example: !friend Ninja"
    )
    async def add(self, ctx: fortnitepy.ext.commands.Context, *, epic_username: str) -> None:
        user = await self.fetch_user(epic_username)

        if user is not None:
            await self.add_friend(user.id)
            await ctx.send(f'Sent/accepted friend request to/from {user.display_name}.')
            print(f'Sent/accepted friend request to/from {user.display_name}.')
        else:
            await ctx.send(f'Cant to find user with the name: {epic_username}.')
            print(
                crayons.red(f"[ERROR] Failed to find a user with the name {epic_username}."))

    @commands.dm_only()
    @commands.command(
        description="[Party] Sets the lobbies selected playlist using playlist name.",
        help="Sets the lobbies selected playlist using playlist name.\n"
             "Example: !playlist Food Fight"
    )
    async def playlist(self, ctx: fortnitepy.ext.commands.Context, *, playlist_name: str) -> None:
        try:
            scuffedapi_playlist_id = await self.fortnite_api.get_playlist(playlist_name)

            if scuffedapi_playlist_id is not None:
                await self.party.set_playlist(playlist=scuffedapi_playlist_id)
                await ctx.send(f'Playlist set to {scuffedapi_playlist_id}.')
                print(f'Playlist set to {scuffedapi_playlist_id}.')

            else:
                await ctx.send(f'Cant find a playlist with the name: {playlist_name}.')
                print(crayons.red(f"[ERROR] "
                                  f"Failed to find a playlist with the name: {playlist_name}."))

        except fortnitepy.errors.Forbidden:
            await ctx.send(f"Failed to set playlist to {playlist_name}, as I'm not party leader.")
            print(crayons.red(f"[ERROR] "
                              "Failed to set playlist as I need leader."))     

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to Golden Peely "
                    "(shortcut for !enlightened CID_701_Athena_Commando_M_BananaAgent 2 350).",
        help="Sets the outfit of the client to Golden Peely.\n"
             "Example: !goldenpeely"
    )
    async def goldenpeely(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.set_outfit(
            asset='CID_701_Athena_Commando_M_BananaAgent',
            variants=self.party.me.create_variants(progressive=4),
            enlightenment=(2, 350)
        )

        await ctx.send(f'Skin set to Golden Peely.')

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the backpack of the client to Purple Ghost Portal.",
        help="Sets the backpack of the client to Purple Ghost Portal.\n"
             "Example: !purpleportal"
    )
    async def purpleportal(self, ctx: fortnitepy.ext.commands.Context) -> None:
        skin_variants = self.party.me.create_variants(
            item='AthenaBackpack',
            particle_config='Particle',
            particle=1
        )

        await self.party.me.set_backpack(
            asset='BID_105_GhostPortal',
            variants=skin_variants
        )

        await ctx.send('To get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!')
        print(f"Backpack set to Purple Ghost Portal.")

    @commands.dm_only()
    @commands.command(
        description="[Party] Sets the readiness of the client to ready.",
        help="Sets the readiness of the client to ready.\n"
             "Example: !ready"
    )
    async def ready(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.set_ready(fortnitepy.ReadyState.READY)
        await ctx.send('Ready to do anything!')   

    @commands.dm_only()
    @commands.command(
        description="[Party] Sets the readiness of the client to unready.",
        help="Sets the readiness of the client to unready.\n"
             "Example: !unready"
    )
    async def unready(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.set_unready(fortnitepy.ReadyState.UNREADY)
        await ctx.send('Unready finaly!')     

    @commands.dm_only()
    @commands.command(
        aliases=['unhide'],
        description="[Party] Promotes the defined user to party leader. If friend is left blank, "
                    "the message author will be used.",
        help="Promotes the defined user to party leader. If friend is left blank, the message author will be used.\n"
             "Example: !promote Terbau"
    )
    async def promote(self, ctx: fortnitepy.ext.commands.Context, *, epic_username: Optional[str] = None) -> None:
        if epic_username is None:
            user = await self.fetch_user(ctx.author.display_name)
            member = self.party.members.get(user.id)
        else:
            user = await self.fetch_user(epic_username)
            member = self.party.members.get(user.id)

        if member is None:
            await ctx.send("Failed to find that user, are you sure they're in the party?")
        else:
            try:
                await member.promote()
                await ctx.send(f"Promoted user: {member.display_name}.")
                print(f"Promoted user: {member.display_name}")
            except fortnitepy.errors.Forbidden:
                await ctx.send(f"Failed topromote {member.display_name}, as I'm not party leader.")
                print(crayons.red(f"[ERROR] "
                                  "Failed to kick member as I don't have the required permissions."))

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets pickaxe using PICKAXE_ID or display name & does 'Point it Out'. If no pickaxe is "
                    "specified, only the emote will be played.",
        help="Sets pickaxe using PICKAXE_ID or display name & does 'Point it Out'. If no pickaxe is "
             "specified, only the emote will be played.\n"
             "Example: !point Pickaxe_ID_029_Assassin"
    )
    async def point(self, ctx: fortnitepy.ext.commands.Context, *, content: Optional[str] = None) -> None:
        if content is None:
            await self.party.me.set_emote(asset='EID_IceKing')
            await ctx.send(f'Point it Out played.')
        elif 'pickaxe_id' in content.lower():
            await self.party.me.set_pickaxe(asset=content)
            await self.party.me.set_emote(asset='EID_IceKing')
            await ctx.send(f'Pickaxe set to {content} & Point it Out played.')
        else:
            try:
                cosmetic = await self.fortnite_api.cosmetics.get_cosmetic(
                    lang="en",
                    searchLang="en",
                    matchMethod="contains",
                    name=content,
                    backendType="AthenaPickaxe"
                )

                await self.party.me.set_pickaxe(asset=cosmetic.id)
                await self.party.me.clear_emote()
                await self.party.me.set_emote(asset='EID_IceKing')
                await ctx.send(f'Pickaxe set to {content} & Point it Out played.')
            except FortniteAPIAsync.exceptions.NotFound:
                await ctx.send(f"Cant find a pickaxe with the name: {content}")

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the backpack of the client using BID.",
        help="Sets the backpack of the client using BID.\n"
             "Example: !bid BID_023_Pinkbear"
    )
    async def b(self, ctx: fortnitepy.ext.commands.Context, backpack_id: str) -> None:
        await self.party.me.set_backpack(
            asset=backpack_id
        )

        await ctx.send(f'Backbling set to {backpack_id}!')

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the emote of the client using EID.",
        help="Sets the emote of the client using EID.\n"
             "Example: !eid EID_Floss"
    )
    async def e(self, ctx: fortnitepy.ext.commands.Context, emote_id: str) -> None:
        await self.party.me.clear_emote()
        await self.party.me.set_emote(
            asset=emote_id
        )

        await ctx.send(f'Emote set to {emote_id}!')


    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Creates the variants list by the variants you set.",
        help="Creates the variants list by the variants you set.\n"
             "Example: !variants CID_030_Athena_Commando_M_Halloween clothing_color 1"
    )
    async def variants(self, ctx: fortnitepy.ext.commands.Context, cosmetic_id: str, variant_type: str,
                       variant_int: str) -> None:
        if 'c' in cosmetic_id.lower() and 'jersey_color' not in variant_type.lower():
            skin_variants = self.party.me.create_variants(
                **{variant_type: int(variant_int) if variant_int.isdigit() else variant_int}
            )

            await self.party.me.set_outfit(
                asset=cosmetic_id,
                variants=skin_variants
            )

        elif 'c' in cosmetic_id.lower() and 'jersey_color' in variant_type.lower():
            cosmetic_variants = self.party.me.create_variants(
                pattern=0,
                numeric=69,
                **{variant_type: int(variant_int) if variant_int.isdigit() else variant_int}
            )

            await self.party.me.set_outfit(
                asset=cosmetic_id,
                variants=cosmetic_variants
            )

        elif 'b' in cosmetic_id.lower():
            cosmetic_variants = self.party.me.create_variants(
                item='AthenaBackpack',
                **{variant_type: int(variant_int) if variant_int.isdigit() else variant_int}
            )

            await self.party.me.set_backpack(
                asset=cosmetic_id,
                variants=cosmetic_variants
            )
        elif 'p' in cosmetic_id.lower():
            cosmetic_variants = self.party.me.create_variants(
                item='AthenaPickaxe',
                **{variant_type: int(variant_int) if variant_int.isdigit() else variant_int}
            )

            await self.party.me.set_pickaxe(
                asset=cosmetic_id,
                variants=cosmetic_variants
            )

        await ctx.send(f'Set variants of {cosmetic_id} to {variant_type} {variant_int}.')
        print(f'Set variants of {cosmetic_id} to {variant_type} {variant_int}.')

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client using CID.",
        help="Sets the outfit of the client using CID.\n"
             "Example: !cid CID_047_Athena_Commando_F_HolidayReindeer"
    )
    async def c(self, ctx: fortnitepy.ext.commands.Context, character_id: str) -> None:
        await self.party.me.set_outfit(
            asset=character_id,
            variants=self.party.me.create_variants(profile_banner='ProfileBanner')
        )

        await ctx.send(f'Skin set to {character_id}.')
        print(f'Skin set to {character_id}.')


    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to Checkered Renegade.",
        help="Sets the outfit of the client to Checkered Renegade.\n"
             "Example: !renegade2"
    )
    async def renegade2(self, ctx: fortnitepy.ext.commands.Context) -> None:
        skin_variants = self.party.me.create_variants(
            material=2
        )

        await self.party.me.set_outfit(
            asset='CID_028_Athena_Commando_F',
            variants=skin_variants
        )

        await ctx.send('To get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN')
        print(f'Skin set to Checkered Renegade.')

    
    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Equips all new non encrypted skins.",
        help="Equips all new non encrypted skins.\n"
             "Example: !new"
    )
    async def new(self, ctx: fortnitepy.ext.commands.Context) -> None:
        new_skins = await self.fortnite_api.cosmetics.get_new_cosmetics()

        for new_skin in [new_cid for new_cid in new_skins if new_cid.split('/')[-1].lower().startswith('cid_')]:
            await self.party.me.set_outfit(
                asset=new_skin.split('/')[-1].split('.uasset')[0]
            )

            await ctx.send(f"Skin set to {new_skin.split('/')[-1].split('.uasset')[0]}!")
            print(f"Skin set to: {new_skin.split('/')[-1].split('.uasset')[0]}!")


        await ctx.send(f'Finished equipping all new unencrypted skins.')
        print(f'Finished equipping all new unencrypted skins.')

        for new_emote in [new_eid for new_eid in new_skins if new_eid.split('/')[-1].lower().startswith('eid_')]:
            await self.party.me.set_emote(
                asset=new_emote.split('/')[-1].split('.uasset')[0]
            )

            await ctx.send(f"Emote set to {new_emote.split('/')[-1].split('.uasset')[0]}!")
            print(f"Emote set to: {new_emote.split('/')[-1].split('.uasset')[0]}!")


        await ctx.send(f'Finished equipping all new unencrypted skins.')
        print(f'Finished equipping all new unencrypted skins.')   
     
    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to a random Henchman skin.",
        help="Sets the outfit of the client to a random Henchman skin.\n"
             "Example: defaults"
    )
    async def defaults(self, ctx: fortnitepy.ext.commands.Context) -> None:
      await ctx.send(f"old defaults..")
      await self.party.me.set_outfit(asset="cid_001_athena_commando_f_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_002_athena_commando_f_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_003_athena_commando_f_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_004_athena_commando_f_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_005_athena_commando_m_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_006_athena_commando_m_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_007_athena_commando_m_default")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_008_athena_commando_m_default")
      await self.party.me.set_emote(asset="EID_Yeet")
      await asyncio.sleep(2.30)
      await ctx.send(f"Chapter 2!!")
      await self.party.me.set_outfit(asset="cid_556_athena_commando_f_rebirthdefaulta")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_557_athena_commando_f_rebirthdefaultb")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_558_athena_commando_f_rebirthdefaultc")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_559_athena_commando_f_rebirthdefaultd")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_560_athena_commando_m_rebirthdefaulta")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_561_athena_commando_m_rebirthdefaultb")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_562_athena_commando_m_rebirthdefaultc")
      await asyncio.sleep(1.30)
      await self.party.me.set_outfit(asset="cid_563_athena_commando_m_rebirthdefaultd")
      await asyncio.sleep(1.30)

      await ctx.send(
        f"There was all defaults! "
    ) 

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to a random Henchman skin.",
        help="Sets the outfit of the client to a random Henchman skin.\n"
             "Example: exclusive"
    )
    async def exclusive(self, ctx: fortnitepy.ext.commands.Context) -> None:
      await ctx.send(f"Exclusive skins..")
      await self.party.me.set_outfit(asset="CID_114_Athena_Commando_F_TacticalWoodland")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_HipHop01")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_174_Athena_Commando_F_CarbideWhite")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_LookAtThis")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_175_Athena_Commando_M_Celestial")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_HandsUp")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_183_Athena_Commando_M_ModernMilitaryRed")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_TwistDaytona")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_342_Athena_Commando_M_StreetRacerMetallic")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_JanuaryBop")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_313_Athena_Commando_M_KpopFashion")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_Kpopdance03")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_386_Athena_Commando_M_StreetOpsStealth")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_Bollywood")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_434_Athena_Commando_F_StealthHonor")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_MathDance")
      await asyncio.sleep(7)
      await ctx.send(f"To get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!")
      await self.party.me.set_outfit(asset="CID_371_Athena_Commando_M_SpeedyMidnight")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_LasagnaDance")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_479_Athena_Commando_F_Davinci")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_Davinci")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_516_Athena_Commando_M_BlackWidowRogue")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_TorchSnuffer")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_757_Athena_Commando_F_WildCat")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_Saxophone")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_441_Athena_Commando_F_CyberScavengerBlue")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_Sprinkler")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_113_Athena_Commando_M_BlueAce")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_PopLock")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_052_Athena_Commando_F_PSBlue")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_HotStuff")
      await asyncio.sleep(7)
      await self.party.me.set_outfit(asset="CID_360_Athena_Commando_M_TechOpsBlue")
      await asyncio.sleep(2)
      await self.party.me.set_emote(asset="EID_Dab")
      await asyncio.sleep(7)

      await ctx.send(
        f"There was all exclusive!"
    ) 
    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Equips all skins currently in the item shop.",
        help="Equips all skins currently in the item shop.\n"
             "Example: !shop"
    )
    async def shop(self, ctx: fortnitepy.ext.commands.Context) -> None:
        store = await self.fetch_item_shop()

        await ctx.send(f"Equipping all skins in today's item shop.")
        print(f"Equipping all skins in today's item shop.")

        for item in store.special_featured_items + \
                store.special_daily_items + \
                store.special_featured_items + \
                store.special_daily_items:
            for grant in item.grants:
                if grant['type'] == 'AthenaCharacter':
                    await self.party.me.set_outfit(
                        asset=grant['asset']
                    )

                    await ctx.send(f"Skin set to {item.display_names[0]}!")
                    print(f"Skin set to: {item.display_names[0]}!")


        await ctx.send(f'Finished equipping all skins in the item shop.')
        print(f'Finished equipping all skins in the item shop.')

    @commands.dm_only()
    @commands.command(
        description="[Party] Sends the defined user a friend request.",
        help="Sends the defined user a friend request.\n"
             "Example: !friend GhostLeaks"
    )
    async def friend(self, ctx: fortnitepy.ext.commands.Context, *, epic_username: str) -> None:
        user = await self.fetch_user(epic_username)

        if user is not None:
            await self.add_friend(user.id)
            await ctx.send(f'Sent/accepted friend request to/from {user.display_name}.')
            print(f'Sent/accepted friend request to/from {user.display_name}.')
        else:
            await ctx.send(f'Cant find a user with the name: {epic_username}.')
            print(
                crayons.red(f"[ERROR] Failed to find a user with the name {epic_username}."))
    
    @commands.dm_only()
    @commands.command(
        name="invite",
        description="[Party] Invites the defined friend to the party. If friend is left blank, "
                    "the message author will be used.",
        help="Invites the defined friend to the party.\n"
             "Example: !invite Terbau"
    )
    async def _invite(self, ctx: fortnitepy.ext.commands.Context, *, epic_username: Optional[str] = None) -> None:
        if epic_username is None:
            epic_friend = self.get_friend(ctx.author.id)
        else:
            user = await self.fetch_user(epic_username)

            if user is not None:
                epic_friend = self.get_friend(user.id)
            else:
                epic_friend = None
                await ctx.send(f'Cant find a user with the name: {epic_username}.')
                print(crayons.red(f"[ERROR] "
                                  f"Failed to find user with the name: {epic_username}."))

        if isinstance(epic_friend, fortnitepy.Friend):
            try:
                await epic_friend.invite()
                await ctx.send(f'Invited {epic_friend.display_name} to the party.')
                print(f"[ERROR] Invited {epic_friend.display_name} to the party.")
            except fortnitepy.errors.PartyError:
                await ctx.send('Failed to invite friend as they are either already in the party or it is full.')
                print(crayons.red(f"[ERROR] "
                                  "Failed to invite to party as friend is already either in party or it is full."))
        else:
            await ctx.send('Cannot invite to party as the friend is not found.')
            print(crayons.red(f"[ERROR] "
                              "Failed to invite to party as the friend is not found."))
                      
    @commands.dm_only()
    @commands.command(
        description="[Party] Joins the party of the defined friend. If friend is left blank, "
                    "the message author will be used.",
        help="Joins the party of the defined friend.\n"
             "Example: !join Terbau"
    )
    async def join(self, ctx: fortnitepy.ext.commands.Context, *, epic_username: Optional[str] = None) -> None:
        if epic_username is None:
            epic_friend = self.get_friend(ctx.author.id)
        else:
            user = await self.fetch_user(epic_username)

            if user is not None:
                epic_friend = self.get_friend(user.id)
            else:
                epic_friend = None
                await ctx.send(f'Failed to find user with the name: {epic_username}.')

        if isinstance(epic_friend, fortnitepy.Friend):
            try:
                await epic_friend.join_party()
                await ctx.send(f'Joined the party of {epic_friend.display_name}.')
            except fortnitepy.errors.Forbidden:
                await ctx.send('Failed to join party since it is private.')
            except fortnitepy.errors.PartyError:
                await ctx.send('Party not found, are you sure party is pubblic?')
        else:
            await ctx.send('Cannot join party as the friend is not found.')        
    
    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Clears/stops the emote currently playing.",
        help="Clears/stops the emote currently playing.\n"
             "Example: !stop"
    )
    async def stop(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.clear_emote()
        await ctx.send('Ok I stop doing everything!')

    @commands.dm_only()
    @commands.command(
        description="[Party] Sets the parties current privacy.",
        help="Sets the parties current privacy.\n"
             "Example: !privacy private"
    )
    async def privacy(self, ctx: fortnitepy.ext.commands.Context, privacy_type: str) -> None:
        try:
            if privacy_type.lower() == 'public':
                await self.party.set_privacy(fortnitepy.PartyPrivacy.PUBLIC)
            elif privacy_type.lower() == 'private':
                await self.party.set_privacy(fortnitepy.PartyPrivacy.PRIVATE)
            elif privacy_type.lower() == 'friends':
                await self.party.set_privacy(fortnitepy.PartyPrivacy.FRIENDS)
            elif privacy_type.lower() == 'friends_allow_friends_of_friends':
                await self.party.set_privacy(fortnitepy.PartyPrivacy.FRIENDS_ALLOW_FRIENDS_OF_FRIENDS)
            elif privacy_type.lower() == 'private_allow_friends_of_friends':
                await self.party.set_privacy(fortnitepy.PartyPrivacy.PRIVATE_ALLOW_FRIENDS_OF_FRIENDS)

            await ctx.send(f'Party privacy set to {self.party.privacy}.')
            print(f'Party privacy set to {self.party.privacy}.')

        except fortnitepy.errors.Forbidden:
            await ctx.send(f"Failed to set party privacy to {privacy_type}, as I'm not party leader.")
            print(crayons.red(f"[ERROR] "
                              "Failed to set party privacy as I don't have the required permissions."))

    @commands.dm_only()
    @commands.command(
        description="[Party] Kicks the inputted user.",
        help="Kicks the inputted user.\n"
             "Example: !kick GhostLeaks"
    )
    async def kick(self, ctx: fortnitepy.ext.commands.Context, *, epic_username: str) -> None:
        user = await self.fetch_user(epic_username)
        member = self.party.members.get(user.id)

        if member is None:
            await ctx.send("Failed to find that user, are you sure they're in the party?")
        else:
            try:
                await member.kick()
                await ctx.send(f"Kicked user: {member.display_name}.")
                print(f"Kicked user: {member.display_name}")
            except fortnitepy.errors.Forbidden:
                await ctx.send(f"I can't kick {member.display_name}, as I'm not party leader.")
                print(crayons.red(f"[ERROR] "
                                  "Failed to kick member as I don't have the required permissions."))

    @commands.dm_only()
    @commands.command(
        description="[Party] Sets the level of the self.",
        help="Sets the level of the self.\n"
             "Example: !level 999"
    )
    async def level(self, ctx: fortnitepy.ext.commands.Context, banner_level: int) -> None:
        await self.party.me.set_banner(
            season_level=banner_level
        )

        await ctx.send(f'Set level to {banner_level}. \nTo get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!')
    
    @commands.dm_only()
    @commands.command(
        description="[Party] Leaves the current party.",
        help="Leaves the current party.\n"
             "Example: !leave"
    )
    async def leave(self, ctx: fortnitepy.ext.commands.Context) -> None:
        await self.party.me.set_emote('EID_Snap')
        await asyncio.sleep(2.0)
        await self.party.me.leave()
        await ctx.send('Bye!')

        print(f'Left the party as I was requested.')

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to Pink Ghoul Trooper.",
        help="Sets the outfit of the client to Pink Ghoul Trooper.\n"
             "Example: !pinkghoul"
    )
    async def pinkghoul(self, ctx: fortnitepy.ext.commands.Context) -> None:
        skin_variants = self.party.me.create_variants(
            material=3
        )

        await self.party.me.set_outfit(
            asset='CID_029_Athena_Commando_F_Halloween',
            variants=skin_variants
        )

        await ctx.send('To get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!')
        print(f"Skin set to Pink Ghoul Trooper.") 

    @commands.dm_only()
    @commands.command(
        description="[Cosmetic] Sets the outfit of the client to Purple Skull Trooper.",
        help="Sets the outfit of the client to Purple Skull Trooper.\n"
             "Example: !purpleskull"
    )
    async def purpleskull(self, ctx: fortnitepy.ext.commands.Context) -> None:
        skin_variants = self.party.me.create_variants(
            clothing_color=1
        )

        await self.party.me.set_outfit(
            asset='CID_030_Athena_Commando_M_Halloween',
            variants=skin_variants
        )

        await ctx.send('To get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n3) TikTok: Ghost_Leaks\n4) Instagram: ghost__leaks\nMade with GhostFN!')
        print(f"Skin set to Purpleskull.")

    @commands.dm_only()
    @commands.command()
    async def skin(self, ctx: fortnitepy.ext.commands.Context, *, content: str):
        try:
            cosmetic = await self.fortnite_api.cosmetics.get_cosmetic(
                lang="en",
                searchLang="en",
                matchMethod="contains",
                name=content,
                backendType="AthenaCharacter"
            )

            print(f"[>] Set skin to: {cosmetic.id}.")
            await self.party.me.set_outfit(asset=cosmetic.id)

        except FortniteAPIAsync.exceptions.NotFound:
            
            print(f"[!] Failed to find a skin with the name: {content}.")

    @commands.dm_only()
    @commands.command()
    async def backpack(self, ctx: fortnitepy.ext.commands.Context, *, content: str):
        try:
            cosmetic = await self.fortnite_api.cosmetics.get_cosmetic(
                lang="en",
                searchLang="en",
                matchMethod="contains",
                name=content,
                backendType="AthenaBackpack"
            )

            print(f"[>] Set backpack to: [{cosmetic.id}]")
            await self.party.me.set_backpack(asset=cosmetic.id)

        except FortniteAPIAsync.exceptions.NotFound:
            print(f"[!] Failed to find a backpack with the name: [{content}]")

    @commands.dm_only()
    @commands.command()
    async def emote(self, ctx: fortnitepy.ext.commands.Context, *, content: str):
        try:
            cosmetic = await self.fortnite_api.cosmetics.get_cosmetic(
                lang="en",
                searchLang="en",
                matchMethod="contains",
                name=content,
                backendType="AthenaDance"
            )

            print(f"[>] Set emote to: {cosmetic.id}.")
            await self.party.me.clear_emote()
            await self.party.me.set_emote(asset=cosmetic.id)

        except FortniteAPIAsync.exceptions.NotFound:
            print(f"[!] Failed to find an emote with the name: [{content}]")


if os.getenv("EMAIL") and os.getenv("PASSWORD"):
    bot = EasyBot(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD")
    )

    bot.run()
    print(f"[>] Bot is ready")
else:
    sys.stderr.write("[!] Enter an Email and Password in the \".env\" file.\n")
    sys.exit()
