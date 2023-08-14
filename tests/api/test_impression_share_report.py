import pytest
from datetime import datetime

# Assuming the split_date_range function is defined in a module named 'date_utils.py'
from tap_apple_search_ads.api.impression_share_reports import split_date_range

def test_split_date_range():
    # Test normal scenario
    result = split_date_range(datetime(2023, 1, 1), datetime(2023, 4, 15))
    expected = [
        (datetime(2023, 1, 1), datetime(2023, 1, 30)),
        (datetime(2023, 1, 31), datetime(2023, 3, 1)),
        (datetime(2023, 3, 2), datetime(2023, 3, 31)),
        (datetime(2023, 4, 1), datetime(2023, 4, 15))
    ]
    assert result == expected
