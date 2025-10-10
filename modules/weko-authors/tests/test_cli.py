import pytest
from click.testing import CliRunner
from weko_authors.cli import authors, AuthorIndexer

# Mock AuthorIndexer for testing
@pytest.fixture
def mock_author_indexer(mocker):
    mock_indexer = mocker.patch("weko_authors.cli.AuthorIndexer", autospec=True)
    instance = mock_indexer.return_value
    instance.bulk_process_authors = mocker.Mock()
    return instance

@pytest.fixture
def default_es_bulk_kwargs():
    return {
        "raise_on_error": True,
        "raise_on_exception": True,
        "chunk_size": 500,
        "max_chunk_bytes": 104857600,
        "max_retries": 0,
        "initial_backoff": 2,
        "max_backoff": 600,
        "stats_only": False
    }

# --yes-i-know not specified
@pytest.mark.parametrize("input_value", ["N", "n"])
def test_reindex_prompt_exit(script_info, mock_author_indexer, input_value):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex"], input=input_value, obj=script_info)
    assert "Do you really want to reindex all records?" in result.output
    assert result.exit_code == 1
    mock_author_indexer.bulk_process_authors.assert_not_called()

# --yes-i-know specified
def test_reindex_skip_prompt(script_info, mock_author_indexer):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know"], obj=script_info)
    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once()

# --file or -f specified
@pytest.mark.parametrize("flag", ["--file", "-f"])
def test_reindex_with_file(script_info, mock_author_indexer, tmp_path, default_es_bulk_kwargs, flag):
    file_path = tmp_path / "uuids.txt"
    file_path.write_text("uuid1\nuuid2\nuuid3")

    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", flag, str(file_path)], obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once_with(
        default_es_bulk_kwargs, ["uuid1", "uuid2", "uuid3"], None, None, True
    )

# --id specified
def test_reindex_with_id(script_info, mock_author_indexer, default_es_bulk_kwargs):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--id", "uuid1"], obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once_with(
        default_es_bulk_kwargs, ["uuid1"], None, None, True
    )

# --start-date specified
@pytest.mark.parametrize("input,expected", [
    ("2025-01-01T01:10:10", "2025-01-01T01:10:10"),
    ("2025-01-01", "2025-01-01T00:00:00"),
    ("2025-01", "2025-01-01T00:00:00"),
    ("2025", "2025-01-01T00:00:00"),
])
def test_reindex_with_start_date(script_info, mock_author_indexer, default_es_bulk_kwargs, input, expected):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--start-date", input], obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once_with(
        default_es_bulk_kwargs, [], expected, None, True
    )

# --end-date specified
@pytest.mark.parametrize("input,expected", [
    ("2025-01-01T01:10:10", "2025-01-01T01:10:10"),
    ("2025-01-02", "2025-01-02T00:00:00"),
    ("2025-02", "2025-02-01T00:00:00"),
    ("2026", "2026-01-01T00:00:00"),
])
def test_reindex_with_end_date(script_info, mock_author_indexer, default_es_bulk_kwargs, input, expected):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--end-date", input], obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once_with(
        default_es_bulk_kwargs, [], None, expected, True
    )

# --with-deleted specified
@pytest.mark.parametrize("args,expected", [
    ([], True),
    (["--with-deleted=True"], True),
    (["--with-deleted=False"], False),
])
def test_reindex_with_with_deleted(script_info, mock_author_indexer, default_es_bulk_kwargs, args, expected):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know"] + args, obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once_with(
        default_es_bulk_kwargs, [], None, None, expected
    )

# Elasticsearch parameters
def test_reindex_with_es_bulk_kwargs(script_info, mock_author_indexer):
    runner = CliRunner()
    cli_args = [
        "reindex", "--yes-i-know", "--raise-on-error=False",
        "--raise-on-exception=False", "--chunk-size=50", "--max-retries=1"
    ]

    expected_es_bulk_kwargs = {
        'raise_on_error': False,
        'raise_on_exception': False,
        'chunk_size': 50,
        'max_chunk_bytes': 104857600,
        'max_retries': 1,
        'initial_backoff': 2,
        'max_backoff': 600,
        'stats_only': False
    }

    result = runner.invoke(authors, cli_args, obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once_with(
        expected_es_bulk_kwargs, [], None, None, True
    )

# Normal execution
def test_reindex_normal_execution(script_info, mock_author_indexer):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know"], obj=script_info)

    assert result.exit_code == 0
    mock_author_indexer.bulk_process_authors.assert_called_once()
    assert "Authors reindexed successfully." in result.output

# --yes-i-know not specified, invalid input
def test_reindex_prompt_invalid_input(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex"], input="z", obj=script_info)

    assert "Error: invalid input" in result.output
    assert "Do you really want to reindex all records?" in result.output
    assert result.exit_code == 1

# --file and --id specified together
def test_reindex_file_and_id_together(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--file", "path/to/file", "--id", "uuid1"], obj=script_info)

    assert "Cannot use both --file and --id options together." in result.output
    assert result.exit_code == 2


# --file without value
def test_reindex_file_without_value(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--file"], obj=script_info)

    assert "Error: --file option requires an argument" in result.output
    assert result.exit_code == 2

# --file specifies a non-existent file
def test_reindex_file_non_existent(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--file", "non_existent_file.txt"], obj=script_info)

    assert "File non_existent_file.txt does not exist." in result.output
    assert result.exit_code == 2

# --file specifies a file with unreadable values
def test_reindex_file_unreadable_values(script_info, tmp_path, mock_author_indexer):
    file_path = tmp_path / "unreadable_values.txt"
    file_path.write_bytes(b"\xff\xfe\xfa")  # Invalid binary content

    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--file", str(file_path)], obj=script_info)

    assert f"Error reading file {file_path}: " in result.output
    assert result.exit_code == 2

# --file specifies an empty file
def test_reindex_file_empty(script_info, tmp_path):
    file_path = tmp_path / "empty_file.txt"
    file_path.write_text("")

    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--file", str(file_path)], obj=script_info)

    assert "Error: No UUIDs were found for processing." in result.output
    assert result.exit_code == 2

# --id without value
def test_reindex_id_without_value(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--id"], obj=script_info)

    assert "Error: --id option requires an argument" in result.output
    assert result.exit_code == 2

# --start-date without value
def test_reindex_start_date_without_value(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--start-date"], obj=script_info)

    assert "Error: --start-date option requires an argument" in result.output
    assert result.exit_code == 2

# --start-date specifies an out-of-range date
def test_reindex_start_date_out_of_range(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--start-date", "2025-02-30"], obj=script_info)

    assert "Error: --start-date option is out of range." in result.output
    assert result.exit_code == 2

# --start-date specifies an invalid format
def test_reindex_start_date_invalid_format(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--start-date", "225"], obj=script_info)

    assert "Error: The format of the --start-date option is incorrect." in result.output
    assert result.exit_code == 2

# --end-date without value
def test_reindex_end_date_without_value(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--end-date"], obj=script_info)

    assert "Error: --end-date option requires an argument" in result.output
    assert result.exit_code == 2

# --end-date specifies an out-of-range date
def test_reindex_end_date_out_of_range(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--end-date", "2025-13"], obj=script_info)

    assert "Error: --end-date option is out of range." in result.output
    assert result.exit_code == 2

# --end-date specifies an invalid format
def test_reindex_end_date_invalid_format(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--end-date", "aaa"], obj=script_info)

    assert "Error: The format of the --end-date option is incorrect." in result.output
    assert result.exit_code == 2

# --start-date is later than --end-date
def test_reindex_start_date_later_than_end_date(script_info):
    runner = CliRunner()
    result = runner.invoke(authors, ["reindex", "--yes-i-know", "--start-date", "2025", "--end-date", "2024"], obj=script_info)

    assert "Error: The --start-date must be earlier than the --end-date." in result.output
    assert result.exit_code == 2


def test_normalize_date():
    from weko_authors.cli import normalize_date

    assert normalize_date("2025-01-01T01:10:10") == "2025-01-01T01:10:10"
    assert normalize_date("2025-01-01") == "2025-01-01T00:00:00"
    assert normalize_date("2025-01") == "2025-01-01T00:00:00"
    assert normalize_date("2025") == "2025-01-01T00:00:00"
    assert normalize_date("") is None
    assert normalize_date(None) is None

    with pytest.raises(ValueError):
        normalize_date("invalid-date")
