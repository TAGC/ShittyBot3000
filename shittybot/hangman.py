import random

from discord.ext import commands


class HangmanCog(object):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._session = None

    @commands.group(pass_context=True)
    async def hangman(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.help()

    @hangman.command
    async def help(self):
        return await self._bot.say(
            '**!hangman start**: start a new Hangman game\n'
            '**!hangman stop**: stop current Hangman game\n'
            '**!hangman guess**: guess letter or word')

    @hangman.command
    async def start(self):
        if not self._session:
            return await self._bot.say('Hangman session already in progress')

        self._session = Hangman(['foo', 'bar', 'baz'])
        await self._bot.say('Started new hangman session...```\n{}```'.format(self._session))

    @hangman.command
    async def stop(self):
        if not self._session:
            return await self._bot.say('No hangman session in progress')

        await self._bot.say('Hangman session ended')
        self._session = None

    @hangman.command(pass_context=True)
    async def guess(self, ctx, letter_or_word: str):
        if not self.hangman:
            return await self._bot.say('No hangman session in progress')

        member = ctx.message.author
        answer = self._session.answer

        self._session.guess(letter_or_word)

        if self._session.is_game_won():
            self._bot.say('Congratulations {0}! The word was {1}'.format(member, answer))
        elif self._session.is_game_lost():
            self._bot.say('Unlucky! The word was {1}'.format(member, answer))
        else:
            self._bot.say('```{}```'.format(self._session))


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
        return self._guesses_made >= self._max_guesses

    @property
    def _max_guesses(self):
        return len(self.STATES) - 1

    @property
    def _guesses_made(self):
        return len(self._guessed_letters) + len(self._guessed_words)

    def guess(self, letter_or_word: str):
        if self.is_game_over:
            raise Exception('Hangman game is over')

        if len(letter_or_word) == 1:
            self._guessed_letters.add(letter_or_word)
        else:
            self._guessed_words.add(letter_or_word)

    def __repr__(self):
        figure = self.STATES[self._guesses_made]
        hidden_answer = ' '.join(l if l in self._guessed_letters else _ for l in self.answer)
        guesses = ', '.join(guess for guess in self._guessed_letters.union(self._guessed_words))

        return '{}{}\nGuessed: {}'.format(figure, hidden_answer, guesses)
