try:
    from typing import Any, Union, Optional

    import asyncio
    import datetime
    import json
    import functools
    import random as py_random
    import subprocess
    import os
    import asyncio
    import uvloop
    import sys

    from fortnitepy.ext import commands

    import aioconsole
    import crayons
    import fortnitepy
    import FortniteAPIAsync
    import sanic
    import aiohttp
except ModuleNotFoundError:
    print(f'[!] Error found, run: install.bat')


sanic_app = sanic.Sanic(__name__) #mxnty is best
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

class EasyBot(commands.Bot):
    def __init__(self, email : str, password : str, **kwargs):
        self.status = 'Made with GhostFN 👻'
        self.kairos = '	cid_017_57be3d12193366eacf9d41c198a97dc66c214ffdfa47776539ac0431ad57b656'
        device_auth_details = get_device_auth_details().get(email, {})
        super().__init__(
            command_prefix='/',
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

        self.welcome_message = ""


    async def set_and_update_member_prop(self, schema_key: str, new_value: Any):
        prop = {schema_key: self.party.me.meta.set_prop(schema_key, new_value)}

        await self.party.me.patch(updated=prop)

    async def set_and_update_party_prop(self, schema_key: str, new_value: Any):
        prop = {schema_key: self.party.me.meta.set_prop(schema_key, new_value)}

        await self.party.patch(updated=prop)


    async def event_ready(self):
        global name

        name = self.user.display_name

        print(crayons.green(f'[>] Logged in as: [{self.user.display_name}].'))

        coro = self.sanic_app.create_server(
            host='0.0.0.0',
            port=8000,
           return_asyncio_server=True,
            access_log=False
        )
        self.server = await coro

        for pending in self.incoming_pending_friends:
            epic_friend = await pending.accept()
            if isinstance(epic_friend, fortnitepy.Friend):
                print(f"[+] Accepted friend request from: [{epic_friend.display_name}]")
            else:
                print(f"[!] Declined friend request from: [{pending.display_name}]")

    async def event_party_invite(self, invite: fortnitepy.ReceivedPartyInvitation):
        await invite.accept()
        print(f'[>] Joined: {invite.sender.display_name}.')

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

                await self.party.send(f"Welcome, [{member.display_name}], \n to get your OWN Lobby Bot: \n1) Join our Discord at: https://discord.gg/8AHPRyEzmF \n2)YouTube: Ghost Leaks\n TikTok: Ghost_Leaks\n Instagram: ghost__leaks\nMade with GhostFN!")
            
                print(f"[+] [{member.display_name}] Joined the Lobby.")

    async def event_friend_message(self, message: fortnitepy.FriendMessage):
        print(f'{message.author.display_name}: {message.content}')
        await message.reply(self.welcome_message.replace('{DISPLAY_NAME}', message.author.display_name))

    async def event_command_error(self, ctx: fortnitepy.ext.commands.Context,
                                  error: fortnitepy.ext.commands.CommandError):
        if isinstance(error, fortnitepy.ext.commands.errors.CommandNotFound):
            if isinstance(ctx.message, fortnitepy.FriendMessage):
                await ctx.send('Invalid Command!')
            else:
                pass
        elif isinstance(error, fortnitepy.ext.commands.errors.MissingRequiredArgument):
            await ctx.send('Error, I need permissions :)')
        elif isinstance(error, fortnitepy.ext.commands.errors.PrivateMessageOnly):
            pass
        else:
            raise error

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
else:
    sys.stderr.write("[!] Enter an Email and Password in the \".env\" file.\n")
    sys.exit()
