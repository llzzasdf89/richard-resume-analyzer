import pytest

from models.analyses import transition_analysis_status


def test_allows_queued_to_processing():
    assert transition_analysis_status("queued", "processing") == "processing"


def test_rejects_processing_back_to_queued():
    with pytest.raises(ValueError, match="Invalid analysis state transition"):
        transition_analysis_status("processing", "queued")


def test_allows_completed_to_deleted():
    assert transition_analysis_status("completed", "deleted") == "deleted"
