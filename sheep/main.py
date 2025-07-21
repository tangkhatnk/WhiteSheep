import discord
import json
from discord.ext import commands
from discord import app_commands

with open('data/config.json', 'r', encoding = 'utf-8') as data:
    config = json.load(data)
    if config:
        token = config['TOKEN']
        default_prefix = config['PREFIX']
    
intents = discord.Intents.all()

bot = commands.Bot(
    intents = intents,
    command_prefix = default_prefix,
    help_command = None,
)

cogs: list[str] = [
    "cogs.utils.help",
    "cogs.economy.create_acc",
    "cogs.economy.daily",
    "cogs.economy.check",
    "cogs.economy.taixiu",
    "cogs.economy.give",
    "cogs.economy.topcoin",
    "cogs.economy.cf",
    "cogs.economy.luck",
    "cogs.economy.baucua",
]

async def load_cogs() -> None:
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            cog_name = cog.split(".",)[-1]
            print(f'💚 Đã tải Cog: {cog_name} 💚')
            
        except Exception as error:
            print(f'💔Không thể tải Cog {cog}. Lỗi: {error}')
            
@bot.event
async def on_ready() -> None:
    await load_cogs()
    await bot.tree.sync()
    print(f'cừu {bot.user} đã lên')
    
bot.run(token)