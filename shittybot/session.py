from typing import Callable, Any

from discord import Channel


class SessionManager(object):
    def __init__(self, session_factory: Callable[[], Any]):
        self._sessions = dict()
        self._create_session = session_factory

    def session_exists_for_channel(self, channel: Channel):
        return channel in self._sessions

    def get_session(self, channel: Channel):
        if not self.session_exists_for_channel(channel):
            raise ValueError(channel)

        return self._sessions[channel]

    def create_session(self, channel: Channel):
        if self.session_exists_for_channel(channel):
            raise ValueError(channel)

        self._sessions[channel] = self._create_session()

    def get_or_create_session(self, channel: Channel):
        if not self.session_exists_for_channel(channel):
            self._sessions[channel] = self._create_session()

        return self._sessions[channel]

    def destroy_session(self, channel: Channel):
        if not self.session_exists_for_channel(channel):
            raise ValueError(channel)

        del self._sessions[channel]
