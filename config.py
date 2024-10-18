from dataclasses import dataclass
from typing import List 
import tomllib
import os

@dataclass
class BotConfig:
    token : str
    status : str
    database : str
    admins : List[int]

def load_config() -> BotConfig:
    with open('config.toml' , "rb") as file:
        config = tomllib.load(file)
        return BotConfig(**config[os.getenv('BOT_ENV' , 'dev')])

config : BotConfig = load_config()    

