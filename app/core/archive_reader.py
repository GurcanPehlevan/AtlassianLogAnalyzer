from __future__ import annotations

import gzip
import zipfile
from pathlib import Path

from app.core.models import LogSource


SUPPORTED_EXTENSIONS = {".log", ".txt", ".out", ".gz", ".zip"}
TEXT_EXTENSIONS = {".log", ".txt", ".out"}


class ArchiveReader:
    def read_paths(self, paths: list[Path]) -> list[LogSource]:
        sources: list[LogSource] = []
        for path in paths:
            if path.is_dir():
                sources.extend(self._read_directory(path))
            elif path.is_file():
                sources.extend(self._read_file(path))
        return sources

    def _read_directory(self, directory: Path) -> list[LogSource]:
        sources: list[LogSource] = []
        for path in directory.rglob("*"):
            if path.is_file() and self._is_supported(path):
                sources.extend(self._read_file(path))
        return sources

    def _read_file(self, path: Path) -> list[LogSource]:
        suffix = path.suffix.lower()
        if suffix == ".zip":
            return self._read_zip(path)
        if suffix == ".gz":
            return [LogSource(path.name, str(path), self._read_gzip_text(path))]
        if suffix in TEXT_EXTENSIONS:
            return [LogSource(path.name, str(path), self._read_text(path))]
        return []

    def _read_zip(self, path: Path) -> list[LogSource]:
        sources: list[LogSource] = []
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                inner = Path(info.filename)
                suffix = inner.suffix.lower()
                if suffix not in TEXT_EXTENSIONS and suffix != ".gz":
                    continue
                data = archive.read(info)
                if suffix == ".gz":
                    content = gzip.decompress(data).decode("utf-8", errors="replace")
                else:
                    content = data.decode("utf-8", errors="replace")
                sources.append(LogSource(inner.name, f"{path}!/{info.filename}", content))
        return sources

    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")

    def _read_gzip_text(self, path: Path) -> str:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def _is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTENSIONS
