# -*- coding: utf-8 -*-


import json
import logging
import os
import random
import time
import datetime


class global_args:
    """ Global statics """
    OWNER = "Mystique"
    ENVIRONMENT = "production"
    MODULE_NAME = "get_square"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    ANDON_CORD_PULLED = False


def set_logging(lv=global_args.LOG_LEVEL):
    """ Helper to enable logging """
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(level=lv)
    return logger


# Initial some defaults in global context to reduce lambda start time, when re-using container
logger = set_logging()


def _sleep_for(max_seconds=10):
    logger.info(f"sleep_start_time:{str(datetime.datetime.now())}")
    time.sleep(max_seconds)
    logger.info(f"sleep_end_time:{str(datetime.datetime.now())}")


def _get_square(n: int = 1) -> int:
    """ Return square of given integer """
    q = 0
    if isinstance(n, int) and n > 0:  # If n is an integer or a float
        q = n*n
    return q


def lambda_handler(event, context):
    logger.debug(f"recvd_event:{event}")

    s = random.randint(13, 81)

    _sleep_for(1)

    # Get Path Parameter
    if "number" in event:
        s = _get_square(int(event.get("number")))
    else:
        s = f"; sent me this evnt: {json.dumps(event)}"

    msg = {
        "statusCode": 200,
        "square": s
    }

    logger.info(f"{msg}")

    return msg
