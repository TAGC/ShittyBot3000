import random
import re
import textwrap

from discord.ext import commands

from shittybot.session import SessionManager


class HangmanCog(object):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._sessions = SessionManager(lambda: Hangman(self._word_list))

        with open('hangman.dat') as f:
            self._word_list = f.read().splitlines()

    @property
    def _usage(self):
        return ('**!hangman start**: start a new Hangman game\n'
                '**!hangman stop**: stop current Hangman game\n'
                '**!hangman guess**: guess letter or word')

    @commands.group(pass_context=True)
    async def hangman(self, ctx):
        if ctx.invoked_subcommand is None:
            channel = ctx.message.channel
            if not self._sessions.session_exists_for_channel(channel):
                await self._bot.say(self._usage)
            else:
                guess = await self._try_parse_hangman_guess('^.hangman\s+(?P<guess>\w+)\s*$', ctx.message.content)
                await self._make_guess(ctx.message.author, channel, guess)

    @hangman.command()
    async def help(self):
        await self._bot.say(self._usage)

    @hangman.command(pass_context=True)
    async def start(self, ctx):
        channel = ctx.message.channel
        if self._sessions.session_exists_for_channel(channel):
            return await self._bot.say('Hangman session already in progress')

        session = self._sessions.get_or_create_session(channel)
        await self._bot.say('Started new hangman session...```\n{}```'.format(session))

    @hangman.command(pass_context=True)
    async def stop(self, ctx):
        channel = ctx.message.channel
        if not self._sessions.session_exists_for_channel(channel):
            return await self._bot.say('No hangman session in progress')

        await self._bot.say('Hangman session ended')
        self._sessions.destroy_session(channel)

    @hangman.command(pass_context=True)
    async def guess(self, ctx, letter_or_word: str):
        author = ctx.message.author
        channel = ctx.message.channel
        await self._make_guess(author, channel, letter_or_word)

    async def _try_parse_hangman_guess(self, pattern, content):
        try:
            return re.match(pattern, content).group('guess')
        except AttributeError:
            await self._bot.say('Invalid guess: "{}"'.format(content))

    async def _make_guess(self, user, channel, letter_or_word):
        try:
            session = self._sessions.get_session(channel)
        except ValueError:
            return await self._bot.say('No hangman session in progress')

        answer = session.answer

        session.guess(letter_or_word)

        if session.is_game_won:
            await self._bot.say(
                '```{}```\nCongratulations {}! The word was "{}"'.format(session, user.name, answer))
            self._sessions.destroy_session(channel)

        elif session.is_game_lost:
            await self._bot.say('```{}```\nUnlucky! The word was "{}"'.format(session, answer))
            self._sessions.destroy_session(channel)

        else:
            await self._bot.say('```{}```'.format(session))


class Hangman(object):
    STATES = [
        r'''
            ------
            |/
            |
            |
            |
            |
            |
        ---------
        ''',
        r'''
            ------
            |/   |
            |
            |
            |
            |
            |
        ---------
        ''',
        r'''
            ------
            |/   |
            |    0
            |
            |
            |
            |
        ---------
        ''',
        r'''
            ------
            |/   |
            |    0
            |   \|
            |
            |
            |
        ---------
        ''',
        r'''
            ------
            |/   |
            |    0
            |   \|/
            |
            |
            |
        ---------
        ''',
        r'''
            ------
            |/   |
            |    0
            |   \|/
            |    |
            |   /
            |
        ---------
        ''',
        r'''
            ------
            |/   |
            |    0
            |   \|/
            |    |
            |   / \
            |
        ---------
        '''
    ]

    def __init__(self, possible_words):
        self.answer = random.choice(possible_words).lower()
        self._guessed_letters = set()
        self._guessed_words = set()

    @property
    def is_game_over(self):
        return self.is_game_lost or self.is_game_won

    @property
    def is_game_won(self):
        return any(word == self.answer for word in self._guessed_words) or \
               all(letter in self._guessed_letters for letter in self.answer)

    @property
    def is_game_lost(self):
        return self._wrong_guesses >= self._max_guesses

    @property
    def _max_guesses(self):
        return len(self.STATES) - 1

    @property
    def _wrong_guesses(self):
        return sum(1 for l in self._guessed_letters if l not in self.answer) + \
               sum(1 for w in self._guessed_words if w != self.answer)

    def guess(self, letter_or_word: str):
        if self.is_game_over:
            raise Exception('Hangman game is over')

        if len(letter_or_word) == 1:
            self._guessed_letters.add(letter_or_word.lower())
        else:
            self._guessed_words.add(letter_or_word.lower())

    def __repr__(self):
        figure = textwrap.dedent(self.STATES[self._wrong_guesses])
        guesses = ', '.join(sorted(guess for guess in self._guessed_letters.union(self._guessed_words)))

        if self.is_game_over:
            hidden_answer = ' '.join(l for l in self.answer)
        else:
            hidden_answer = ' '.join(l if l in self._guessed_letters else '_' for l in self.answer)

        return '{}\n{}\tGuessed: {}'.format(figure, hidden_answer, guesses)
