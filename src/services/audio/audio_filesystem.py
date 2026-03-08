"""Service for connecting to the filesystem, finding audio files, and creating an index of them"""

from pathlib import Path
from typing import List, Optional, Iterable, Iterator, Union
from src.domain.audios.track import AudioTrack

DEFAULT_AUDIO_EXTENSIONS = [
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
    ".aac",
]


class AudioFilesystem:
    """Class to handle OS audio files for the bot using domain `AudioTrack`.

    Notes:
    - `is_explicit` is inferred from the first path component relative to `audio_path`.
    """

    def __init__(self, audio_path: Union[str, Path], extensions: Optional[List[str]] = None, recursive: bool = True, explicit_folder: Optional[str] = "explicit"):
        self.audio_path = Path(audio_path)
        self.extensions = [extensions.lower() for extensions in (extensions if extensions is not None else DEFAULT_AUDIO_EXTENSIONS)]
        self.recursive = recursive
        self.explicit_folder = explicit_folder.lower() if explicit_folder is not None else None
        self._tracks: List[AudioTrack] = []
        self.load_index()

    def load_index(self) -> int:
        """Scan the audios folder"""
        self._tracks.clear()
        if not self.audio_path.exists():
            return 0

        iterator = self.audio_path.rglob("*") if self.recursive else self.audio_path.glob("*")
        for file_path in iterator:
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.extensions:
                continue

            # determine explicitness by relative first component if explicit_folder configured
            is_explicit = False
            if self.explicit_folder is not None:
                try:
                    rel_path = file_path.relative_to(self.audio_path)
                    if rel_path.parts:
                        is_explicit = (rel_path.parts[0].lower() == self.explicit_folder)
                except Exception:
                    is_explicit = False

            self._tracks.append(AudioTrack(path=file_path, is_explicit=is_explicit))

        return len(self._tracks)

    def get_all(self) -> List[AudioTrack]:
        """Return a copy of the list of indexed tracks."""
        return list(self._tracks)

    def find_by_name(self, query: str) -> List[AudioTrack]:
        """Case-insensitive substring search over track file names (stem)."""
        query = query.lower()
        return [track for track in self._tracks if query in track.path.stem.lower()]

    def __len__(self) -> int:
        return len(self._tracks)

    def __iter__(self) -> Iterator[AudioTrack]:
        yield from self._tracks