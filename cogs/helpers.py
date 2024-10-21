import discord
from functools import partial
from typing import List , Any , TYPE_CHECKING
if TYPE_CHECKING:
    from main import TmrModMail
from sqlalchemy import select
from models import Ticket    

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
        title = self.title_input.value
        topic = self.topic_input.value
        await interaction.response.defer()
        forum = interaction.client.get_channel(int(interaction.client.config.forum_id))
        if not forum:
            await interaction.followup.send(content="Failed to created modmail forum channel not found..." , ephemeral=True)
        else:
            try:
                embed = discord.Embed(title="ModMail Request" , color=discord.Color.green())
                embed.add_field(name="User" , value=f"{interaction.user.name} ID : `{interaction.user.id}`")
                embed.add_field(name="Subject" , value=title[:1000] , inline=False)
                embed.add_field(name="Reason" , value=topic[:1000] , inline=False)
                embed.timestamp = discord.utils.utcnow()
                content=f"<@&{int(interaction.client.config.staff_role)}>"
                thread_channel = await forum.create_thread(name=f"{interaction.user.name}-modmail" , content=content , embed=embed)
                embed = discord.Embed(color=discord.Color.green())
                embed.title = "ModMail Thread Created"
                embed.description = f"Please wait a few second until our staff will look your ticket . You can type your issue here our staff will review it soon."
                await interaction.channel.send(embed=embed)
                await interaction.message.delete()
                async with interaction.client.db_session() as session:
                    ticket = Ticket()
                    ticket.guild_id = forum.guild.id
                    ticket.thread_id = thread_channel.thread.id
                    ticket.user_id = interaction.user.id
                    session.add(ticket)
                    await session.commit()
            except discord.HTTPException as e:
                await interaction.followup.send(content=f"Failed to create thread : {e.text[:1700]}" , ephemeral=True)

                    
    
            




  