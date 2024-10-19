import discord
from functools import partial
from typing import List , Any , TYPE_CHECKING
if TYPE_CHECKING:
    from main import TmrModMail

class ModMailOpenView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Open ModMail Thread" , emoji="📨" , style=discord.ButtonStyle.red)
    async def open_modmail_button(self , interaction : discord.Interaction["TmrModMail"] , button : discord.ui.Button[Any])  -> None:
        await interaction.response.send_modal(ModMailModal(title="TMR ModMail" , timeout=90 , custom_id="modal"))

class ModMailModal(discord.ui.Modal):
    def __init__(self, *, title: str = ..., timeout: float | None = None, custom_id: str = ...) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.title_input = discord.ui.TextInput(label="Enter ModMail Topic" , style=discord.TextStyle.long , required=True)
        self.topic_input = discord.ui.TextInput(label="Enter ModMail Description" , style=discord.TextStyle.paragraph , required=True)
        self.add_item(self.title_input)
        self.add_item(self.topic_input)

    async def on_submit(self, interaction: discord.Interaction["TmrModMail"]) -> None:
        title = self.title_input
        topic = self.topic_input
        await interaction.response.defer()
        forum = interaction.client.get_channel(int(interaction.client.config.forum_id))
        print(type(forum))
        if not forum:
            await interaction.followup.send(content="Failed to created modmail forum channel not found..." , ephemeral=True)
        else:
            try:
                thread = await forum.create_thread(name=f"{interaction.user.name}-modmail")
                await thread.send(content=f"<@&{int(interaction.client.config.staff_role)}>\n*User : {interaction.user.name} (ID : {interaction.user.id})\n* Subject : {title}\n* Reason : {topic}")
                await interaction.followup.send(content="Created ModMail send messsage here you message will be automatically forwarded to modmail channel" , ephemeral=True)
            except discord.HTTPException as e:
                await interaction.response.send_message(content=f"Failed to create thread : {e[:1700]}" , ephemeral=True)

                    
    
            




  