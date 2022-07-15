import logging
import typing as tp
from datetime import datetime

from rich.console import ConsoleRenderable
from rich.logging import RichHandler as _RichHandler
from rich.traceback import Traceback


class RichHandler(_RichHandler):
    """Custom rich logging handler that prints logger name instead of path in the
    most right column.
    """

    def __init__(self, **kwargs) -> None:
        """Set some usefull defaults for handler config."""
        kwargs.update({"rich_tracebacks": True, "enable_link_path": True})
        super().__init__(**kwargs)

    def render(
        self,
        *,
        record: logging.LogRecord,
        traceback: tp.Optional[Traceback],
        message_renderable: ConsoleRenderable,
    ) -> ConsoleRenderable:
        """Override how rich renders logs, instead of setting logger filepath as the
        rightmost column, we set the name of logger.
        Parameters
        ----------
        record : logging.LogRecord
        traceback : tp.Optional[Traceback]
        message_renderable : ConsoleRenderable
        Returns
        -------
        ConsoleRenderable
        """

        path = record.name
        level = self.get_level_text(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)

        log_renderable = self._log_render(
            self.console,
            [message_renderable] if not traceback else [message_renderable, traceback],
            log_time=log_time,
            time_format=time_format,
            level=level,
            path=path,
            link_path=record.pathname if self.enable_link_path else None,
        )
        return log_renderable
