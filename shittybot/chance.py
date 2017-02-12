import random

from discord.ext import commands


class ChanceCog(object):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.command(pass_context=True)
    async def roll(self, ctx, sides: int = 6):
        user = ctx.message.author
        roll = random.randint(1, sides)
        await self._bot.say('{} rolled {}'.format(user.name, roll))

    @commands.command(pass_context=True)
    async def flip(self, ctx):
        user = ctx.message.author
        flip = random.choice(('Heads', 'Tails'))
        await self._bot.say('{} flipped {}'.format(user.name, flip))
