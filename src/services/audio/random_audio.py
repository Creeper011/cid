"""Service for picking random audio tracks to play in voice channels by Audio Filesystem"""
import random
from pathlib import Path
from typing import Optional, Iterable
from src.services import AudioFilesystem
from src.domain.audios.track import AudioTrack


class RandomAudio():
	"""class to pick an random audio on file system"""

	def __init__(self, audio_filesystem: Optional[AudioFilesystem] = None, audio_path: Optional[str] = None, allow_explicit: bool = False):
		if audio_filesystem is not None:
			self.fs = audio_filesystem
		else:
			path = Path(audio_path) if audio_path is not None else (Path.cwd() / "audios")
			self.fs = AudioFilesystem(path)
		self.allow_explicit = allow_explicit

	def pick(self, exclude_playing: Optional[Iterable[Path]] = None, allow_explicit: Optional[bool] = None) -> AudioTrack:
		"""Return an `AudioTrack` chosen at random.

		- `exclude_playing`: iterable of Path to exclude from selection
		- `allow_explicit`: overrides the instance default if provided
		"""
		allow_explicit = self.allow_explicit if allow_explicit is None else allow_explicit
		exclude_paths = set(Path(p) for p in (exclude_playing or []))

		candidates = [t for t in self.fs.get_all() if (allow_explicit or not t.is_explicit) and t.path not in exclude_paths]
		if not candidates:
			raise LookupError("No audio tracks available after applying filters")
		return random.choice(candidates)

	def pick_path(self, exclude_playing: Optional[Iterable[Path]] = None, allow_explicit: Optional[bool] = None) -> Path:
		"""Return the filesystem path of a random track."""
		return self.pick(exclude_playing=exclude_playing, allow_explicit=allow_explicit).path
