import logging

from discord.ext import commands

from shittybot.config import TOKEN
from shittybot.hangman import HangmanCog
from shittybot.hotorcold import HotOrColdCog
from shittybot.chance import ChanceCog

bot = commands.Bot(command_prefix='!', description="ThymineC's shitty bot")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot.add_cog(HangmanCog(bot))
    bot.add_cog(HotOrColdCog(bot))
    bot.add_cog(ChanceCog(bot))
    bot.run(TOKEN)
