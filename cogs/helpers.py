import discord
from functools import partial
from typing import List , Any , TYPE_CHECKING
if TYPE_CHECKING:
    from main import TmrModMail

class MutualGuildSelector(discord.ui.View):
    def __init__(self, *, timeout: float | None = 90 , modmail_guilds : List[discord.Guild] ):
        self.modmail_guilds = modmail_guilds
        self.selected : discord.Guild | None = None
        super().__init__(timeout=timeout)
        for guild in self.modmail_guilds:
            button : discord.ui.Button[Any] = discord.ui.Button(label=guild.name[:75] , style=discord.ButtonStyle.primary , custom_id=str(guild.id))
            self.add_item(button)
            self.children[-1].callback = partial(self.callback , button) # type: ignore

    async def callback(self , interaction : discord.Interaction["TmrModMail"] , button : discord.ui.Button[Any]) -> None:
        await interaction.response.defer()
        assert button.custom_id
        self.selected = interaction.client.get_guild(int(button.custom_id))
        self.stop()

class OpenModMailView(discord.ui.View):
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Open ModMail Thread" , emoji="🎫" , style=discord.ButtonStyle.red , custom_id="thread:open")
    async def open_modmail_thread(self , interaction : discord.Interaction["TmrModMail"] , button : discord.ui.Button[Any]) -> None:
        pass

class CloseModMailView(discord.ui.View):
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Close ModMail Thread" , emoji="🚮" , style=discord.ButtonStyle.red , custom_id="thread:close")
    async def close_modmail_thread(self , interaction : discord.Interaction["TmrModMail"] , button : discord.ui.Button[Any]) -> None:
        pass    



  