from __future__ import annotations
from typing import TYPE_CHECKING , Optional
if TYPE_CHECKING:
    from main import TmrModMail
from discord.ext import commands  
import discord  
from sqlalchemy import select , delete
from models import Ticket as TicketModel , ModMailBlacklist as ModMailBlacklistModel 
from discord import app_commands
from .helpers import ModMailOpenView
from contextlib import suppress

class ModMail(commands.Cog):
    def __init__(self , bot : "TmrModMail") -> None:
        super().__init__()
        self.bot = bot

    async def getch_user(self , user_id : int) -> Optional[discord.User]:
        try:
            user = self.bot.get_user(user_id)
            if not user:
                user = await self.bot.fetch_user(user_id)
            return user
        except (discord.HTTPException , discord.Forbidden , discord.InvalidData , discord.NotFound):
            return None    

    # @commands.Cog.listener()
    # async def on_command_error(self , ctx : commands.Context , error : commands.CommandError):
    #     await ctx.reply(content=f"Panic!({error})")

    @commands.Cog.listener()
    async def on_message(self , message : discord.Message ) -> None:
        if message.author.bot:
            return
        
        if not message.guild:
            async with self.bot.db_session() as session:
                item = await session.execute(select(ModMailBlacklistModel).where(ModMailBlacklistModel.user_id == message.author.id))
                bl_user = item.scalar_one_or_none()
                if bl_user:
                    print("[-] Ignoring message as user is blacklisted from the guild modmail.")
                    return
                result = await session.execute(select(TicketModel).where(TicketModel.user_id == message.author.id))
                ticket = result.scalar_one_or_none()
                if ticket:
                    print("[-] Ticket already exists forwarding user message...")
                    channel = self.bot.get_channel(ticket.thread_id)
                    if channel:
                        print("[-] Forwarded user message to the ticket...")
                        file = await message.attachments[0].to_file() if message.attachments else None
                        await channel.send(content=f"**💬 {message.author.name} :** {message.content[:1800]}", file= file , allowed_mentions=discord.AllowedMentions.none())  
                else:
                    print("[-] Send panel to open modmail....")
                    embed = discord.Embed(color=discord.Color.green())
                    embed.title = f"{self.bot.get_channel(self.bot.config.forum_id).guild.name} ModMail"
                    embed.description = f"Welcome, {message.author.mention}! You can use this menu to contact the staff members of the server.\n You may use this menu to report people or ask questions from the moderators.\n Keep in mind that abusing this may lead to punishments!"
                    embed.set_footer(text="Click the button below to open a ticket !")
                    await message.reply(embed=embed , view=ModMailOpenView(timeout=None))
        else:
            async with self.bot.db_session() as session:
                result = await session.execute(select(TicketModel).where(TicketModel.thread_id == message.channel.id))
                thread = result.scalar_one_or_none()
                if thread:
                    user = await self.getch_user(thread.user_id)
                    if user:
                        try:
                            file = await message.attachments[0].to_file() if message.attachments else None
                            await user.send(content=f"**{message.guild.name} Staff:** {message.content[:1800]}" , file=file )
                        except discord.Forbidden as e:
                            await message.reply(content=f"🔴 I'm unable to send this message to **{user.name}** : `{e}`")
                    
                            
    
                                           

    
    @commands.Cog.listener()
    async def on_member_remove(self , member : discord.Member) -> None:
        async with self.bot.db_session() as session:
            result = await session.execute(select(TicketModel).where(TicketModel.user_id == member.id , TicketModel.guild_id == member.guild.id))
            ticket = result.scalar_one_or_none()
            if ticket:
                channel = self.bot.get_channel(ticket.thread_id)
                if channel:
                    await channel.send(content=f"🔒 **{member.name}** left server. Use `/close` to close this thread.")



     

    

    @commands.hybrid_command(name="close")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @app_commands.allowed_contexts(guilds=True , dms=False)
    async def modmail_close(self , ctx : commands.Context["TmrModMail"] , toggle : bool) -> None:
        """Close the current modmail ticket."""
        await ctx.defer()
        async with self.bot.db_session() as session:
            if self.bot.config.staff_role in [r.id for r in ctx.author.roles] or ctx.author.guild_permissions.manage_threads:

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
            else:
                embed = discord.Embed(color=discord.Color.red())
                embed.description = f"You are missing staff role or `manage_threads` permissions to close this thread."
                await ctx.reply(embed=embed)


    @commands.hybrid_command(name="modmail-clear")
    @commands.cooldown(1 , 4, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    async def modmail_clear(self , ctx : commands.Context["TmrModMail"] , user : discord.User) -> None:
        """Clear modmail data of a user."""
        await ctx.defer()
        async with self.bot.db_session() as session:
            stmt = delete(TicketModel).where(TicketModel.user_id == user.id , TicketModel.guild_id == ctx.guild.id)
            await session.execute(stmt)
            await session.commit()
        embed = discord.Embed(color=discord.Color.green())
        embed.description = f"Successfully deleted all modmail data realated to **{user.name}#0**"
        await ctx.reply(embed=embed)


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
                    embed = discord.Embed(color=discord.Color.green())
                    embed.description = f"Successfully unblacklisted **{user.name}**"
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply(content=f"`{user.name}` , is not blacklisted.")
        else:
            async with self.bot.db_session() as session:
                item = ModMailBlacklistModel()
                item.user_id = user.id
                item.guild_id = ctx.guild.id
                session.add(item)
                await session.commit()
            embed = discord.Embed(color=discord.Color.green())
            embed.description = f"Successfully blacklisted **{user.name}**"
            await ctx.reply(embed=embed)

         
                        




async def setup(bot : "TmrModMail") -> None:
    await bot.add_cog(ModMail(bot))           
