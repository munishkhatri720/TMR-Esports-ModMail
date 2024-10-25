import argparse
import os
from rich import print
from config import load_config
from discord.ext import commands
from typing import TYPE_CHECKING , List
import discord
if TYPE_CHECKING:
    from config import BotConfig
from sqlalchemy.ext.asyncio import async_sessionmaker , create_async_engine , AsyncSession 
import asyncio   
from models import Base
from discord.utils import setup_logging
from discord.ext import tasks
from cogs.helpers import ModMailCloseView , ModMailOpenView


setup_logging(level=20)



os.environ.setdefault("JISHAKU_HIDE", "1")
os.environ.setdefault("JISHAKU_RETAIN", "1")
os.environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")
os.environ.setdefault("JISHAKU_NO_DM_TRACEBACK", "1")
os.environ.setdefault("JISHAKU_FORCE_PAGINATOR", "1")

class TmrModMail(commands.AutoShardedBot):
    def __init__(self , config : "BotConfig") -> None:
        self._config = config
        super().__init__(command_prefix=self.get_prefix , intents=discord.Intents.all() , owner_ids=config.admins , strip_after_prefix = True , case_insensitive=True)
    
    @property
    def config(self) -> "BotConfig":
        return self._config
    
    async def get_prefix(self, message: discord.Message) -> List[str] | str:
        return commands.when_mentioned (self , message)
    
    async def on_ready(self) -> None:
        print(f"Logged in as {self.user.name} ID : {self.user.id}")
        await self.tree.sync()
        
    @tasks.loop(seconds=10)
    async def change_status(self) -> None:
        await self.change_presence(activity=discord.Game(name=self.config.status))


    
    async def setup_hook(self) -> None:
        await self.connect_db()
        self.loop.create_task(self.load_cogs())
        
        self.change_status.start()
        self.add_view(ModMailOpenView(timeout=None))
        self.add_view(ModMailCloseView(timeout=None))


    async def load_cogs(self) -> None:
        await self.load_extension('cogs.modmail')
        print(f"[-] Loaded all cogs.")

    async def connect_db(self) -> None:
        self.engine = create_async_engine(self.config.database , echo=False)
        self.db_session = async_sessionmaker(bind=self.engine , class_=AsyncSession ,expire_on_commit=False)
        async with self.engine.begin() as engine:
            await engine.run_sync(Base.metadata.create_all)

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

if __name__ == "__main__":
    main()            



    



