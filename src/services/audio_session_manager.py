"""Manages audio sessions for voice channels in guilds"""

from datetime import datetime
from src.domain.audios.audio_session import AudioSession
from src.domain.exceptions.audio_exceptions import SessionAlreadyActiveException

class AudioSessionManager():
    def __init__(self) -> None:
        self._sessions: dict[int, AudioSession] = {}  # guild_id -> session

    def open_session(self, guild_id: int, channel_id: int) -> AudioSession:
        if guild_id in self._sessions:
            raise SessionAlreadyActiveException(guild_id)
        session = AudioSession(guild_id=guild_id, channel_id=channel_id, started_at=datetime.now())
        self._sessions[guild_id] = session
        return session

    def close_session(self, guild_id: int) -> None:
        self._sessions.pop(guild_id, None)

    def get_session(self, guild_id: int) -> AudioSession | None:
        return self._sessions.get(guild_id)

    def has_active_session(self, guild_id: int) -> bool:
        return guild_id in self._sessions

    def get_all_sessions(self) -> dict[int, AudioSession]:
        return dict(self._sessions) # type: ignore