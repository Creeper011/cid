"""Background loop cog to continuously play audio in active voice sessions"""

from discord.ext import commands, tasks
from src.config.config_model import ConfigModel
from src.services import AudioSessionManager, RandomAudio, DiscordVoiceManager
import random

class AudioPlaybackLoop(commands.Cog):
    """Background loop to play audio in active sessions"""

    def __init__(self, bot: commands.Bot, config: ConfigModel, audio_manager: AudioSessionManager,
                 random_audio_service: RandomAudio, voice_manager: DiscordVoiceManager):
        self.bot: commands.Bot = bot
        self.audio_manager: AudioSessionManager = audio_manager
        self.random_audio_service: RandomAudio = random_audio_service
        self.voice_manager: DiscordVoiceManager = voice_manager
        self.config = config
        self._validate_config() # Call the new validation method
        self.background_loop_task = tasks.loop(seconds=self.config.discord.audio_sys.default_interval_seconds)(self.background_loop) # type: ignore
        self.background_loop_task.before_loop(self.before_background_loop)
        self.background_loop_task.start()

    def _validate_config(self) -> None:
        """Validates the necessary configuration parameters."""
        if self.config.discord.audio_sys is None: # type: ignore
            raise ValueError(
                "Missing Configuration: The 'app.discord.audios' section is not defined in the configuration file. "
                "Please ensure this section is properly configured."
            )

        if self.config.discord.audio_sys.default_interval_seconds is None: # type: ignore
            raise ValueError(
                "Missing Configuration: 'default_interval_seconds' is not defined in the 'app.discord.audios' section of the configuration file. "
                "Please define a numeric value for the audio loop interval."
            )
        
        if self.config.discord.audio_sys.default_provability_percent is None: #type: ignore
            raise ValueError(
                "Missing Configuration: 'default_provability_percent' is not defined in the 'app.discord.audios' section of the configuration file. "
                "Please define an integer value between 0 and 100 for the audio provability percent."
            )
        
        provability = self.config.discord.audio_sys.default_provability_percent #type: ignore
        if not (0 <= provability <= 100):
            raise ValueError(
                f"Invalid Configuration: 'default_provability_percent' must be between 0 and 100, but got {provability}. "
                "Please define a valid integer value."
            )

    def cog_unload(self) -> None:  # type: ignore
        self.background_loop_task.cancel()

    async def background_loop(self) -> None:
        for guild_id, session in self.audio_manager.get_all_sessions().items():
            if not self.voice_manager.is_connected(guild_id):
                continue
            if self.voice_manager.is_playing(guild_id):
                continue
            if random.randint(1, 100) > self.config.discord.audio_sys.default_provability_percent:  # type: ignore
                continue
            try:
                track = self.random_audio_service.pick(allow_explicit=session.allow_explicit)
                session.current_track = track
                self.voice_manager.play_audio(guild_id, track.path)
            except LookupError:
                pass

    async def before_background_loop(self) -> None:
        await self.bot.wait_until_ready()