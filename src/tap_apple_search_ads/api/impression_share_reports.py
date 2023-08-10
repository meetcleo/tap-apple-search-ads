import time
import requests
import singer
import csv
from datetime import datetime
from typing import Any, Dict, List

from tap_apple_search_ads import api
from tap_apple_search_ads.api.auth import RequestHeadersValue
from tap_apple_search_ads.api.campaign_level_reports import load_selector, reportsSelector

logger = singer.get_logger()

REPORT_REQUEST_DEFAULT_URL = "https://api.searchads.apple.com/api/v4/custom-reports"
REPORT_FETCH_DEFAULT_URL = "https://api.searchads.apple.com/api/v4/custom-reports/{report_id}"

def sync(
    headers: RequestHeadersValue,
    start_time: datetime,
    selector_name: str,
) -> List[Dict[str, Any]]:

    selector = load_selector(selector_name)

    selector["startTime"] = start_time.strftime(api.API_DATE_FORMAT)
    selector["endTime"] = start_time.strftime(api.API_DATE_FORMAT)
    selector["name"] = "impression_share_reports_via_meltano"

    logger.info(
        "Sync: impression share level reports with start time [%s] and end time [%s]",
        selector["startTime"],
        selector["endTime"]
    )

    if selector_name == "custom_reports_selector":
        logger.info("Sync: using custom reports selector")
    else:
        logger.info("Sync: using {} selector".format(selector_name))

    # First we must request the creation of the report
    try:
        initial_response = requests.post(REPORT_REQUEST_DEFAULT_URL, headers=headers, json=selector) # type: ignore
        initial_response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Error creating report: %s", e)

    initial_response_json = initial_response.json()

    if initial_response_json["error"]:
        logger.error("Error creating report: %s", initial_response_json["error"])

    report_id = initial_response_json["data"]["id"]
    report_state = initial_response_json["data"]["state"]
    # TODO: going to do anything with this?
    report_creation_time = initial_response_json["data"]["creationTime"]

    if report_state == "QUEUED":
        logger.info("Report is queued, waiting for it to be ready")
        time.sleep(10)

    # Second, we fetch the report URI if the report is ready
    metadata_response = requests.get(REPORT_FETCH_DEFAULT_URL.format(report_id=report_id), headers=headers)
    metadata_response_json = metadata_response.json()

    if metadata_response.status_code != 200 or metadata_response_json["error"]:
        logger.error("Error fetching report metadata: %s", metadata_response_json["error"])

    report_download_uri = metadata_response_json["data"]["downloadUri"]

    # Third, we download the report data from the URI
    report_data_response = requests.get(report_download_uri)

    data = []
    reader = csv.DictReader(report_data_response.text.splitlines())
    for row in reader:
        row["lowImpressionShare"] = float(row["lowImpressionShare"])
        row["highImpressionShare"] = float(row["highImpressionShare"])
        row["searchPopularity"] = int(row["searchPopularity"])
        data.append(row)

    return data
