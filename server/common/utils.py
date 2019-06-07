import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def log_exception_then_continue():
    try:
        yield
    except Exception as e:
        logger.exception(e)
