from datetime import datetime

from handler_types import Event
from lastfm import lastfm_handler
from logger import get_logger
from toggl import toggl_handler

from aws_lambda_powertools.utilities.typing import LambdaContext

logger = get_logger(__name__)


def handler(event: Event, _: LambdaContext):
    start, end = event["start"], event["end"]
    logger.info(
        (
            f"backing up data for {unix_time_to_datestring(start)} "
            f"to {unix_time_to_datestring(end)}"
        )
    )

    logger.info("starting last fm handler")
    lastfm_handler(start, end)

    logger.info("starting toggl handler")
    toggl_handler(start, end)


def unix_time_to_datestring(unix_time: int) -> str:
    dt = datetime.fromtimestamp(unix_time)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
