"""Campaign Level Reports"""

import json
import pathlib
from datetime import datetime
from typing import Any, Dict, List

import requests
import singer

from tap_apple_search_ads import api
from tap_apple_search_ads.api.auth import RequestHeadersValue

logger = singer.get_logger()

DEFAULT_URL = "https://api.searchads.apple.com/api/v5/reports/campaigns"

reportsSelector: Dict[str, Any] = {"loaded": False, "data": Dict[str, Any]}


def load_selector(selector_name) -> Dict[str, Any]:
    if reportsSelector["loaded"]:
        reportsSelector["data"]

    path = (
        pathlib.Path(__file__).parent.parent
        / "selectors"
        / "{}.json".format(selector_name)
    ).absolute()

    logger.info(f"Using selector at path: {path}")


    with open(path, "r") as stream:
        reportsSelector["loaded"] = True
        reportsSelector["data"] = json.load(stream)

    return reportsSelector["data"]


def sync(
    headers: RequestHeadersValue,
    start_time: datetime,
    end_time: datetime,
    selector_name: str,
) -> List[Dict[str, Any]]:
    selector = load_selector(selector_name)

    selector["startTime"] = start_time.strftime(api.API_DATE_FORMAT)
    selector["endTime"] = end_time.strftime(api.API_DATE_FORMAT)

    logger.info(
        "Sync: campaign level reports with start time [%s] and end time [%s]",
        start_time,
        end_time,
    )

    if selector_name == "reports_selector":
        logger.info("Sync: using default selector")
    else:
        logger.info("Sync: using {} selector".format(selector_name))

    response = requests.post(DEFAULT_URL, headers=headers, json=selector)
    api.utils.check_response(response)

    # print will pollute stdout and fail downstream targets
    logger.debug(response.json()["data"])

    return response.json()["data"]["reportingDataResponse"]["row"]


def sync_extended_spend_row(
    headers: RequestHeadersValue,
    start_time: datetime,
    end_time: datetime,
    selector_name: str,
) -> List[Dict[str, Any]]:
    report_rows = sync(headers, start_time, end_time, selector_name)
    extended_spend_rows: List[Dict[str, Any]] = []

    for row in report_rows:
        granularity = row["granularity"]
        metadata = row["metadata"]

        for granularity_row in granularity:
            extended_spend_row = dict(granularity_row)
            extended_spend_row["campaignId"] = metadata["campaignId"]
            extended_spend_rows.append(extended_spend_row)

    return extended_spend_rows


def flatten(record: Dict[str, Any]) -> Dict[str, Any]:
    record["avgCPA"] = json.dumps(record["avgCPA"])
    record["avgCPM"] = json.dumps(record["avgCPM"])
    record["avgCPT"] = json.dumps(record["avgCPT"])
    record["localSpend"] = json.dumps(record["localSpend"])

    return record
