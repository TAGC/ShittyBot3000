import random
import re
from discord.ext import commands


class HotOrColdCog(object):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._sessions = dict()

    @property
    def _usage(self):
        return ('**!hotcold start**: start a new Hot Or Cold game\n'
                '**!hotcold stop**: stop current Hot Or Cold game\n'
                '**!hotcold <number>**: guess number')

    @commands.group(pass_context=True)
    async def hotcold(self, ctx):
        if ctx.invoked_subcommand is None:
            channel = ctx.message.channel
            if self._session_for_channel(channel) is None:
                await self._bot.say(self._usage)
            else:
                guess = int(await self._try_parse_guess('^.hotcold\s+(?P<guess>\d+)\s*$', ctx.message.content))
                await self._make_guess(ctx.message.author, channel, guess)

    @hotcold.command()
    async def help(self):
        await self._bot.say(self._usage)

    @hotcold.command(pass_context=True)
    async def start(self, ctx):
        channel = ctx.message.channel
        if self._session_for_channel(channel):
            return await self._bot.say('Hot Or Cold session already in progress')

        min_guess = 0
        max_guess = 100
        num_guesses = 7
        self._sessions[channel] = HotOrCold(min_guess, max_guess, num_guesses)
        await self._bot.say('Started new Hot Or Cold session. Guess a number between {} and {}. You have {} guesses!'
                            .format(min_guess, max_guess, num_guesses))

    @hotcold.command(pass_context=True)
    async def stop(self, ctx):
        channel = ctx.message.channel
        if not self._session_for_channel(channel):
            return await self._bot.say('No Hot Or Cold session in progress')

        await self._bot.say('Hot Or Cold session ended')
        del self._sessions[channel]

    async def _try_parse_guess(self, pattern, content):
        try:
            return re.match(pattern, content).group('guess')
        except AttributeError:
            await self._bot.say('Invalid guess: "{}"'.format(content))

    async def _make_guess(self, user, channel, number):
        session = self._session_for_channel(channel)
        if not session:
            return await self._bot.say('No Hot Or Cold session in progress')

        answer = session.answer

        session.guess(number)

        if session.is_game_won:
            await self._bot.say('Congratulations {}! The number was {}'.format(user.name, answer))
            del self._sessions[channel]

        elif session.is_game_lost:
            await self._bot.say('Unlucky! The number was {}'.format(answer))
            del self._sessions[channel]

        else:
            await self._bot.say('```{}```'.format(session))

    def _session_for_channel(self, channel):
        if channel in self._sessions:
            return self._sessions[channel]
        else:
            return None


class HotOrCold(object):
    def __init__(self, min_guess: int, max_guess: int, allowed_guesses: int):
        if min_guess > max_guess or min(min_guess, max_guess, allowed_guesses) < 0:
            raise ValueError()

        self.answer = random.randint(min_guess, max_guess)
        self._allowed_guesses = allowed_guesses
        self._guesses = []

        guess_range = max_guess - min_guess
        self._bad_guess_diff = guess_range * 0.5
        self._okay_guess_diff = guess_range * 0.1
        self._good_guess_diff = guess_range * 0.05

    @property
    def is_game_over(self):
        return self.is_game_lost or self.is_game_won

    @property
    def is_game_won(self):
        return self.answer in self._guesses

    @property
    def is_game_lost(self):
        return len(self._guesses) >= self._allowed_guesses

    @property
    def _guesses_left(self):
        return self._allowed_guesses - len(self._guesses)

    def guess(self, number: int):
        if self.is_game_over:
            raise Exception('Hot Or Cold game is over')

        self._guesses.append(number)

    def __repr__(self):
        if not self._guesses:
            return '{No guesses made}'

        def diff(x):
            return abs(x - self.answer)

        diffs = [diff(x) for x in self._guesses]
        last_diff = diffs[-1]
        getting_hotter = len(diffs) >= 2 and diffs[-1] < diffs[-2]
        getting_colder = len(diffs) >= 2 and diffs[-1] > diffs[-2]

        output = ''

        if last_diff <= self._good_guess_diff:
            output += 'Very hot'
            if getting_hotter:
                output += ' and getting hotter'
            elif getting_colder:
                output += ' but getting colder'

        elif last_diff <= self._okay_guess_diff:
            output += 'Hot'
            if getting_hotter:
                output += ' and getting hotter'
            elif getting_colder:
                output += ' but getting colder'

        elif last_diff <= self._bad_guess_diff:
            output += 'Cold'
            if getting_hotter:
                output += ' but getting hotter'
            elif getting_colder:
                output += ' and getting colder'

        else:  # Terrible guess
            output += 'Very cold'
            if getting_hotter:
                output += ' but getting hotter'
            elif getting_colder:
                output += ' and getting colder'

        output += ' ({} guesses left)'.format(self._guesses_left)
        return output
