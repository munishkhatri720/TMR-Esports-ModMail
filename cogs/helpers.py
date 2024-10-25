import discord
from functools import partial
from typing import List , Any , TYPE_CHECKING
if TYPE_CHECKING:
    from main import TmrModMail
from sqlalchemy import select
from models import Ticket    

class ModMailCloseView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Close ModMail Thread" , emoji="🔒" , style=discord.ButtonStyle.red , custom_id="close")
    async def close_modmail_button(self , interaction : discord.Interaction["TmrModMail"] , button : discord.ui.Button[Any])  -> None:
        if interaction.client.config.staff_role in [r.id for r in interaction.user.roles] or interaction.user.guild_permissions.manage_threads:
            async with interaction.client.db_session() as session:
                query = select(Ticket).where(Ticket.thread_id == interaction.channel.id)
                result = await session.execute(query)
                ticket = result.scalar_one_or_none()
                if ticket:
                    if isinstance(interaction.channel, discord.Thread):
                        await interaction.channel.delete()
                        try:
                            u = interaction.client.get_user(ticket.user_id) or await interaction.client.fetch_user(ticket.user_id)
                            await u.send(f"🔒 Your modmail thread has been closed by {interaction.user.mention}.")
                        except:
                            pass
                        #await interaction.channel.edit(archived=True)
                    await session.delete(ticket)
                    await session.commit()
                else:
                    await interaction.response.send_message("Failed to close modmail thread, ticket not found in database." , ephemeral=True)
        else:
            await interaction.response.send_message(content="You don't have permissions to close this thread." , ephemeral=True)

        

class ModMailOpenView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Open ModMail Thread" , emoji="📨" , style=discord.ButtonStyle.red , custom_id="open")
    async def open_modmail_button(self , interaction : discord.Interaction["TmrModMail"] , button : discord.ui.Button[Any])  -> None:
        await interaction.response.send_modal(ModMailModal(title="TMR ModMail" , timeout=90 , custom_id="modal"))


class ModMailModal(discord.ui.Modal):
    def __init__(self, *, title: str = ..., timeout: float | None = None, custom_id: str = ...) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.title_input = discord.ui.TextInput(label="Enter ModMail Topic" , style=discord.TextStyle.long , required=True , max_length=800)
        self.topic_input = discord.ui.TextInput(label="Enter ModMail Description" , style=discord.TextStyle.paragraph , required=True , max_length=800)
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
                thread_channel = await forum.create_thread(name=f"{interaction.user.name}-modmail" , content=content , embed=embed , view=ModMailCloseView(timeout=None))
                content = "⏳ Opened a modmail thread for you! Wait patiently for our staff to respond, you'll be notified here!"
                await interaction.channel.send(content=content)
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

                    
    
            




  