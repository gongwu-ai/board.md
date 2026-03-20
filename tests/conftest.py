import pytest
from board_md.store import init_board


@pytest.fixture
def board_dir(tmp_path):
    """Provide a fresh board directory for each test."""
    return init_board(tmp_path)
