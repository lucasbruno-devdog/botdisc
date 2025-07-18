import discord
from discord.ext import commands
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize the bot with a command prefix
bot = commands.Bot(command_prefix='!')

# Load commands from the commands directory
for filename in os.listdir('./src/commands'):
    if filename.endswith('.py'):
        bot.load_extension(f'commands.{filename[:-3]}')

# Event listener for when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

# Run the bot with the token from the environment variables
bot.run(os.getenv('DISCORD_TOKEN'))