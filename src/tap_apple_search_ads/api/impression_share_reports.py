import time
import requests
import singer
import csv
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from tap_apple_search_ads import api
from tap_apple_search_ads.api.auth import RequestHeadersValue
from tap_apple_search_ads.api.campaign_level_reports import load_selector, reportsSelector

logger = singer.get_logger()

REPORT_REQUEST_DEFAULT_URL = "https://api.searchads.apple.com/api/v5/custom-reports"
REPORT_FETCH_DEFAULT_URL = "https://api.searchads.apple.com/api/v5/custom-reports/{report_id}"
TIME_TO_WAIT_FOR_REPORT_SECS = 15
DAILY_REPORT_REQUEST_LIMIT = 10


def sync(
    headers: RequestHeadersValue,
    start_time: datetime,
    end_time: datetime,
    selector_name: str,
) -> List[Dict[str, Any]]:

    selector = load_selector(selector_name)
    date_ranges = split_date_range(start_time, end_time)

    if selector_name == "custom_reports_selector":
        logger.info("Sync: using custom reports selector")
    else:
        logger.info("Sync: using {} selector".format(selector_name))

    # Request report for each pair of dates
    generated_reports = []
    num_requests_made = 0
    for dates in date_ranges:
        new_selector = selector.copy()
        new_selector["startTime"] = dates[0].strftime(api.API_DATE_FORMAT)
        new_selector["endTime"] = dates[1].strftime(api.API_DATE_FORMAT)

        if num_requests_made > DAILY_REPORT_REQUEST_LIMIT:
            logger.info("Sync: reached daily report request limit, wait for 24 hours")
            break

        logger.info(
            "Sync: impression share level reports with start time [%s] and end time [%s]",
            new_selector["startTime"],
            new_selector["endTime"]
        )

        new_selector["name"] = f"impression_share_report_API_{new_selector['startTime']}_{new_selector['endTime']}"
        report_request_response = request_impression_share_report(headers, new_selector)
        num_requests_made += 1
        generated_reports.append(report_request_response)

    combined_records = []
    for report in generated_reports:
        # Second, we fetch the report URI if the report is ready
        report_download_uri = fetch_single_impression_share_report(report['report_id'], headers)
        csv_data = fetch_csv_data(report_download_uri)
        records = to_schema(csv_data, report['report_creation_time'])
        combined_records.extend(records)

    return combined_records

def request_impression_share_report(headers: RequestHeadersValue, selector: Dict[str, Any]) -> Dict[str, str]:
    """Request an impression share report for a given date range

    Returns tuple of (report ID, report creation time)
    """

    try:
        response = requests.post(REPORT_REQUEST_DEFAULT_URL, headers=headers, json=selector) # type: ignore
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error creating report: {e}, {response.text}") # type: ignore
        raise

    response_json = response.json()

    if response_json["error"]:
        logger.error(f"Error creating report: {response_json['error']}")
        raise

    report_id = response_json["data"]["id"]
    report_state = response_json["data"]["state"]
    report_creation_time = response_json["data"]["creationTime"]

    if report_state == "QUEUED":
        logger.info("Report is queued, waiting for it to be ready")
        time.sleep(TIME_TO_WAIT_FOR_REPORT_SECS)

    return {
        "report_id": report_id,
        "report_creation_time": report_creation_time,
    }

def fetch_csv_data(
    report_download_uri: str,
) -> csv.DictReader:
    try:
        response = requests.get(report_download_uri)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching report CSV: {e}, {response.text}") # type: ignore
        raise

    return csv.DictReader(response.text.splitlines())

def to_schema(csv_data, report_creation_time) -> List[Dict[str, Any]]:

    data = []
    for row in csv_data:
        row["lowImpressionShare"] = float(row["lowImpressionShare"])
        row["highImpressionShare"] = float(row["highImpressionShare"])
        row["searchPopularity"] = int(row["searchPopularity"])
        row['extractedAt'] = report_creation_time
        data.append(row)

    return data

def fetch_single_impression_share_report(report_id: str, headers: RequestHeadersValue):

    try:
        metadata_response = requests.get(REPORT_FETCH_DEFAULT_URL.format(report_id=report_id), headers=headers) # type: ignore
        metadata_response.raise_for_status()
        metadata_response_json = metadata_response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching report metadata: {e}, {metadata_response.text}") # type: ignore
        raise
    if metadata_response_json["error"]:
        logger.error("Error fetching report metadata: %s", metadata_response_json["error"])
        raise

    return metadata_response_json["data"]["downloadUri"]

def split_date_range(start_date: datetime, end_date: datetime):
    """
    Splits a date range into tuples of up to 30 days.

    Args:
    - start_date (str): start date in the format 'YYYY-MM-DD'
    - end_date (str): end date in the format 'YYYY-MM-DD'

    Returns:
    - list of tuples: each tuple represents a date range of up to 30 days
    """

    if start_date > end_date:
        raise ValueError("start_date date must be before or the same as end date.")

    date_range = end_date - start_date

    if date_range.days > 30:
        logger.info("Sync: date range is greater than 30 days, splitting date range into 30 day chunks")

    if start_date > end_date:
        raise ValueError("Start date must be before or the same as end date.")

    date_ranges = []
    while start_date <= end_date:
        next_end = min(start_date + timedelta(days=29), end_date)
        date_ranges.append((start_date, next_end))
        start_date = next_end + timedelta(days=1)

    return date_ranges