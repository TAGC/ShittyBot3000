import asyncio
from datetime import datetime, timedelta
from enum import Enum
from itertools import combinations

from discord.ext import commands

from shittybot.session import SessionManager

RpsChoice = Enum('RpsChoice', 'ROCK PAPER SCISSORS')


class RockPaperScissorsCog(object):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._sessions = SessionManager(lambda: RockPaperScissors())

    @property
    def _usage(self):
        return ('**!rps start**: start a new Rock-Paper-Scissors game\n'
                '**!rps [r|rock]**: choose rock\n'
                '**!rps [p|paper]**: choose paper\n'
                '**!rps [s|scissors]**: choose scissors\n')

    @commands.group(pass_context=True)
    async def rps(self, ctx):
        if ctx.invoked_subcommand is None:
            await self._bot.say(self._usage)

    @rps.command()
    async def help(self):
        await self._bot.say(self._usage)

    @rps.command(pass_context=True)
    async def start(self, ctx):
        channel = ctx.message.channel
        if self._sessions.session_exists_for_channel(channel):
            return await self._bot.say('RPS session already in progress')

        message_content = 'Ready?\n'
        message = await self._bot.say(message_content)
        delay = 0.8
        await asyncio.sleep(delay)

        for message_part in ('Rock. ', 'Paper. ', 'Scissors. ', 'GO!'):
            message_content += message_part
            message = await self._bot.edit_message(message, message_content)
            await asyncio.sleep(0.3)

        session = self._sessions.get_or_create_session(channel)
        await session.wait()
        assert session.is_game_over

        choices, wins, draws = session.results

        if not choices:
            await self._bot.say('Game over! No one chose anything')
        elif not wins and not draws:
            await self._bot.say('Game over! There were no wins or draws')
        else:
            response = ('Game over!\n\n```\n'
                        'Choices\n'
                        '-------\n')
            response += '\n'.join(' - {} chose {}'.format(u, c.name.upper()) for u, c in choices)
            response += ('\n\nWins\n'
                         '----\n')
            response += '\n'.join(' - {} beat {}'.format(w, l) for w, l in wins)
            response += ('\n\nDraws\n'
                         '-----\n')
            response += '\n'.join(' - {} drew with {}'.format(d1, d2) for d1, d2 in draws)
            response += '```'

            await self._bot.say(response)

        self._sessions.destroy_session(channel)

    @rps.command(pass_context=True)
    async def r(self, ctx):
        await self._make_choice(ctx.message.author, ctx.message.channel, RpsChoice.ROCK)

    @rps.command(pass_context=True)
    async def rock(self, ctx):
        await self._make_choice(ctx.message.author, ctx.message.channel, RpsChoice.ROCK)

    @rps.command(pass_context=True)
    async def p(self, ctx):
        await self._make_choice(ctx.message.author, ctx.message.channel, RpsChoice.PAPER)

    @rps.command(pass_context=True)
    async def paper(self, ctx):
        await self._make_choice(ctx.message.author, ctx.message.channel, RpsChoice.PAPER)

    @rps.command(pass_context=True)
    async def s(self, ctx):
        await self._make_choice(ctx.message.author, ctx.message.channel, RpsChoice.SCISSORS)

    @rps.command(pass_context=True)
    async def scissors(self, ctx):
        await self._make_choice(ctx.message.author, ctx.message.channel, RpsChoice.SCISSORS)

    async def _make_choice(self, user, channel, choice: RpsChoice):
        try:
            session = self._sessions.get_session(channel)
            choice_name = choice.name.upper()
            if session.can_make_choice(user.name):
                session.make_choice(user.name, choice)
                await self._bot.say('{} chose {}'.format(user.name, choice_name))
            else:
                await self._bot.say('You\'ve already chosen {}, {}'.format(choice_name, user.name))
        except Exception as e:
            await self._bot.say('No RPS session in progress (maybe you were too slow [or fast?!])')
            print(e)
            return


class RockPaperScissors(object):
    play_window = timedelta(seconds=2)
    win_table = {
        RpsChoice.ROCK: RpsChoice.SCISSORS,
        RpsChoice.PAPER: RpsChoice.ROCK,
        RpsChoice.SCISSORS: RpsChoice.PAPER}

    def __init__(self):
        self._start_time = datetime.now()
        self._choices = dict()
        self.is_game_over = False

    @property
    def results(self):
        if not self.is_game_over:
            raise Exception

        perms = list(combinations(self._choices.items(), 2))
        choices = list(self._choices.items())
        wins = [(u1, u2) for (u1, c1), (u2, c2) in perms if self._beats(c1, c2)]
        wins.extend([(u2, u1) for (u1, c1), (u2, c2) in perms if self._beats(c2, c1)])
        draws = [(u1, u2) for (u1, c1), (u2, c2) in perms if c1 == c2]

        return choices, wins, draws

    def can_make_choice(self, user: str):
        return user not in self._choices

    def make_choice(self, user: str, choice: RpsChoice):
        if self.is_game_over:
            raise Exception('Rock Paper Scissors game is over')

        if self.can_make_choice(user):
            self._choices[user] = choice

    async def wait(self):
        await asyncio.sleep(self.play_window.seconds)
        self.is_game_over = True

    def _beats(self, choice_a: RpsChoice, choice_b: RpsChoice):
        return self.win_table[choice_a] == choice_b
