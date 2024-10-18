import argparse
import os
from rich import print
from config import load_config
from discord.ext import commands
from typing import TYPE_CHECKING
import discord
if TYPE_CHECKING:
    from config import BotConfig
from sqlalchemy.ext.asyncio import async_sessionmaker , create_async_engine , AsyncSession 
import asyncio   



os.environ.setdefault("JISHAKU_HIDE", "1")
os.environ.setdefault("JISHAKU_RETAIN", "1")
os.environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")
os.environ.setdefault("JISHAKU_NO_DM_TRACEBACK", "1")
os.environ.setdefault("JISHAKU_FORCE_PAGINATOR", "1")

class TmrModMail(commands.AutoShardedBot):
    def __init__(self , config : "BotConfig") -> None:
        self._config = config
        super().__init__(command_prefix=self.__class__.get_prefix , intents=discord.Intents.all() , owner_ids=config.admins , strip_after_prefix = True , case_insensitive=True)
    
    @property
    def config(self) -> "BotConfig":
        return self._config
    
    async def setup_hook(self) -> None:
        await self.connect_db()
        self.loop.create_task(self.load_cogs())

    async def load_cogs(self) -> None:
        await self.load_extension('cogs.modmail')

    async def connect_db(self) -> None:
        self.engine = create_async_engine(self.config.database , echo=True)
        self.db_session = async_sessionmaker(bind=self.engine , class_=AsyncSession ,expire_on_commit=False)

async def start_bot(config : "BotConfig") -> None:
    async with TmrModMail(config=config) as bot:
        await bot.start(config.token)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev' , action="store_true" , help="Run the bot in dev mode")
    parser.add_argument('--prod' , action="store_true" , help="Run the bot in prod mode")
    args = parser.parse_args()

    if args.dev:
        os.environ.setdefault("BOT_ENV" , 'dev')


    elif args.prod:
        os.environ.setdefault("BOT_ENV" , 'prod')

    else:
        print("Please provide a valid arg : --dev or --prod")
        return
    
    config : "BotConfig" = load_config()
    coro = start_bot(config)

    try:
        asyncio.run(coro)
    except KeyboardInterrupt:
        print("Exit...")
            



    



