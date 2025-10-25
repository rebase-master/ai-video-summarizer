import uuid
import tempfile
from pathlib import Path
from typing import Optional, IO

class TempVideoFile:
    """
    Context manager that writes a Streamlit-uploaded file-like object to a
    temporary file and ensures cleanup.
    Usage:
        with TempVideoFile(uploaded_file) as tmp_path:
            # tmp_path is a Path to local temp file
    """
    def __init__(self, uploaded_file: IO[bytes], original_name: Optional[str] = None):
        self.uploaded_file = uploaded_file
        self.original_name = original_name or getattr(uploaded_file, "name", "upload")
        self._temp_path: Optional[Path] = None

    def __enter__(self) -> Path:
        extension = self._get_extension()
        unique_id = uuid.uuid4().hex[:12]
        suffix = f"_{unique_id}.{extension}"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(self.uploaded_file.read())
        tmp.flush()
        tmp.close()
        self._temp_path = Path(tmp.name)
        return self._temp_path

    def __exit__(self, exc_type, exc, tb):
        if self._temp_path and self._temp_path.exists():
            try:
                self._temp_path.unlink()
            except Exception:
                # in production you might want to log this
                pass

    def _get_extension(self) -> str:
        if "." in self.original_name:
            return self.original_name.split(".")[-1]
        # fall back to mp4
        return "mp4"