import random
import re
import textwrap

from discord.ext import commands


class HangmanCog(object):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._session = None

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
            if self._session is None:
                await self._bot.say(self._usage)
            else:
                guess = await self._try_parse_hangman_guess('^.hangman\s+(?P<guess>\w+)\s*$', ctx.message.content)
                await self._make_guess(ctx.message.author, guess)

    @hangman.command()
    async def help(self):
        await self._bot.say(self._usage)

    @hangman.command()
    async def start(self):
        if self._session:
            return await self._bot.say('Hangman session already in progress')

        self._session = Hangman(self._word_list)
        await self._bot.say('Started new hangman session...```\n{}```'.format(self._session))

    @hangman.command()
    async def stop(self):
        if not self._session:
            return await self._bot.say('No hangman session in progress')

        await self._bot.say('Hangman session ended')
        self._session = None

    @hangman.command(pass_context=True)
    async def guess(self, ctx, letter_or_word: str):
        guess = await self._try_parse_hangman_guess('^\s*(?P<guess>\w+)\s*$', letter_or_word)
        await self._make_guess(ctx.message.author, guess)

    async def _try_parse_hangman_guess(self, pattern, content):
        try:
            return re.match(pattern, content).group('guess')
        except AttributeError:
            await self._bot.say('Invalid guess: "{}"'.format(content))

    async def _make_guess(self, user, letter_or_word):
        if not self.hangman:
            return await self._bot.say('No hangman session in progress')

        answer = self._session.answer

        self._session.guess(letter_or_word)

        if self._session.is_game_won:
            await self._bot.say(
                '```{}```\nCongratulations {}! The word was "{}"'.format(self._session, user.name, answer))
            self._session = None

        elif self._session.is_game_lost:
            await self._bot.say('```{}```\nUnlucky! The word was "{}"'.format(self._session, answer))
            self._session = None

        else:
            await self._bot.say('```{}```'.format(self._session))


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
        self.answer = random.choice(possible_words)
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
            self._guessed_letters.add(letter_or_word)
        else:
            self._guessed_words.add(letter_or_word)

    def __repr__(self):
        figure = textwrap.dedent(self.STATES[self._wrong_guesses])
        guesses = ', '.join(sorted(guess for guess in self._guessed_letters.union(self._guessed_words)))

        if self.is_game_over:
            hidden_answer = ' '.join(l for l in self.answer)
        else:
            hidden_answer = ' '.join(l if l in self._guessed_letters else '_' for l in self.answer)

        return '{}\n{}\tGuessed: {}'.format(figure, hidden_answer, guesses)
