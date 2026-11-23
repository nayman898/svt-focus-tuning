"""Allow one airflow regression or candidate export per machine at a time."""

from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import gettempdir


@contextmanager
def one_job():
    path = Path(gettempdir()) / "focus-svt-codex-airflow.lock"
    with path.open("a+b") as lease:
        lease.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit("Another Codex airflow or export job is running. Run one job at a time.") from None
        yield
