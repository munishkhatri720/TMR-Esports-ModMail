from __future__ import annotations
from typing import TYPE_CHECKING , Optional
if TYPE_CHECKING:
    from main import TmrModMail
from discord.ext import commands  
import discord  
from sqlalchemy import select
from models import Ticket as TicketModel , ModMailBlacklist as ModMailBlacklistModel , ModMail as ModMailModel
from discord import app_commands
from .helpers import MutualGuildSelector , CloseModMailView
from contextlib import suppress

class ModMail(commands.Cog):
    def __init__(self , bot : "TmrModMail") -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self , message : discord.Message ) -> None:
        if message.author.bot or message.guild:
            return
        
        async with self.bot.db_session() as session:
            result = await session.execute(select(Ticket).where(Ticket.user_id == message.author.id))
            tik = result.scalar_one_or_none()
            if tik:
                pass
            else:
                # create a new ticket
                pass
    
    @commands.Cog.listener()
    async def on_member_remove(self , member : discord.Member) -> None:
        pass

    async def getch_channel(self , channel_id : int) -> Optional[discord.Thread]:
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(channel_id)
            return channel
        except discord.Forbidden:
            return None
        except discord.HTTPException:
            return None
        except discord.NotFound:
            return None    

    @commands.hybrid_command(name="close-modmail")   
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=False , dms=True)
    async def close_mymodmail(self , ctx : commands.Context["TmrModMail"]) -> None:
        """Close any opened modmail thread."""
        await ctx.defer()
        async with self.bot.db_session() as session:
            result = await session.execute(select(TicketModel).where(TicketModel.user_id == ctx.author.id))
            items = result.scalars().all()
            mutuals = [g for g in ctx.author.mutual_guilds if g.id in [item.guild_id for item in items]]
        if len(mutuals) == 0:
            await ctx.reply(content="I have no mutual server with you so your all old threads got automatically closed.")
            return    
        view = MutualGuildSelector(timeout=45 , modmail_guilds=mutuals[:24])
        message = await ctx.reply(content="Select any opened modmail for a server that you want to close :" , view=view)
        await view.wait()
        
        with suppress(discord.HTTPException):
                for child in view.children:
                    if isinstance(child , discord.ui.Button):
                        child.disabled = True
                await message.edit(view=view)
        if not view.selected:
            return
        else:
            async with self.bot.db_session() as session:
                result = await session.execute(select(TicketModel).where(TicketModel.guild_id == view.selected.id))
                item = result.scalar_one_or_none()
                if not item:
                    await message.edit(view=None , content=f"No opened modmail thread created by you found on {view.selected.name}")
                else:
                    channel = await self.getch_channel(item.thread_id)
                    if not channel:
                        await session.delete()
                        await session.commit()
                    if channel:
                        await channel.send(content=f"🔴 Thread closed by **{ctx.author.name}**" , view=CloseModMailView(timeout=None))
                    await message.edit(view=None , content="Successfully sent request to server moderator to close your thread." )



    @commands.hybrid_command(name="switch-modmail")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=False , dms=True)
    async def switch_mymodmail(self , ctx : commands.Context["TmrModMail"]) -> None:
        """Switch to different modmail thread."""   

    @commands.hybrid_command(name="modmail-setup")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    @app_commands.allowed_contexts(dms=False , guilds=True)
    async def modmail_setup(self , ctx : commands.Context["TmrModMail"] , thread : discord.Thread , staff_role : discord.Role) -> None:
        """Setup modmail for current server."""
        await ctx.defer()
        async with self.bot.db_session() as session:
            result = await session.execute(select(ModMailModel).where(ModMailModel.id == ctx.guild.id))
            item = result.scalar_one_or_none()
            if item:
                item.thread_id = thread.id
                item.staff_role = staff_role.id
                await session.commit()
                await ctx.reply(content="Successfully updated the old setup data.")
            else:
                item = ModMailModel()
                item.id = ctx.guild.id
                item.thread_id = thread.id
                item.staff_role = staff_role.id
                session.add(item)
                await session.commit()
                await ctx.reply(content=f"Successfully setupped modmail in {thread.mention}")


    @commands.hybrid_command(name="modmail-toggle")
    @commands.cooldown(1 , 4, commands.BucketType.user)    
    @commands.has_guild_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True , dms=False)
    async def modmail_toggle(self , ctx : commands.Context["TmrModMail"] , toggle : bool ) -> None:
        """Temporary enabled/disabled modmail thread creation."""
        await ctx.defer()
        async with self.bot.db_session() as session:
            result = await session.execute(select(ModMailModel).where(ModMailModel.id == ctx.guild.id))
            item = result.scalar_one_or_none()
            if item:
                item.enabled = toggle  
                await session.commit(item)  
                await ctx.reply(content=f"ModMail has been {'enabled' if toggle is True else 'disabled'}")  
            else:
                await ctx.reply(content="Please setup modmail first !")

    @commands.hybrid_command(name="close")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True , dms=False)
    async def modmail_close(self , ctx : commands.Context["TmrModMail"] , toggle : bool) -> None:
        """Close the current modmail ticket."""
        await ctx.defer()
        async with self.bot.db_session() as session:
            result = await session.execute(select(ModMailModel).where(ModMailModel.id == ctx.guild.id))
            data = result.scalar_one_or_none()
            if (not data and not ctx.author.guild_permissions.manage_threads):
                await ctx.reply(content="You are missing `MANAGE_THREADS` permissions.")
                return
            if data.staff_role not in [role.id for role in ctx.author.roles] and not ctx.author.guild_permissions.manage_threads:
                await ctx.reply(content="You are missing the modmail staff role to close this thread.")
                return

            result = await session.execute(select(TicketModel).where(TicketModel.thread_id == ctx.channel.id , TicketModel.guild_id == ctx.guild.id))
            item = result.scalar_one_or_none()
            if item:
                await ctx.reply(content=f"This thread will be closed in a few seconds...")
                await session.delete(item)
                await session.commit()
                if isinstance(ctx.channel , discord.Thread):
                    await ctx.channel.delete()
            else:
                await ctx.reply(content="I looked in the database , this channel is not a modmail thread. I you want to close delete it manually.")



    @commands.hybrid_command(name="modmail-blacklist")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    async def modmail_blacklist(self , ctx : commands.Context["TmrModMail"] , user : discord.User , blacklisted : bool) -> None:
        """Blacklist/Unblacklist a user."""
        await ctx.defer()
        if blacklisted is False:
            async with self.bot.db_session() as session:
                result = await session.execute(select(ModMailBlacklistModel).where(ModMailBlacklistModel.user_id == user.id , ModMailBlacklistModel.guild_id == ctx.guild.id))
                item = result.scalar_one_or_none()
                if item:
                    await session.delete(item)
                    await session.commit()
                    await ctx.reply(content=f"Successfully unblacklisted {user.name} [ID : {user.id}]")
                else:
                    await ctx.reply(content=f"`{user.name}` , is not blacklisted.")
        else:
            async with self.bot.db_session() as session:
                item = ModMailBlacklistModel()
                item.user_id = user.id
                item.guild_id = ctx.guild.id
                session.add(item)
                await session.commit()
            await ctx.reply(content=f"Successfully blacklisted `{user.name}`")  

    @commands.hybrid_command(name="modmail-reset")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    async def modmail_reset(self , ctx : commands.Context["TmrModMail"]) -> None:
        """Reset the modmail setup."""
        async with self.bot.db_session() as session:
            result = await session.execute(select(ModMailModel).where(ModMailModel.id == ctx.guild.id))
            item = result.scalar_one_or_none()     
            if item:
                await session.delete(item)
                await session.commit()
                await ctx.reply(content="Successfully deleted the modmail setup data.")
            else:
                await ctx.reply(content="No setup data found !")         
                        




           
