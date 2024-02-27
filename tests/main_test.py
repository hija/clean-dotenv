from os import DirEntry
from unittest.mock import MagicMock, call, mock_open, patch
import pytest
import clean_dotenv


class DirEntry:
    def __init__(self, path, is_file=True):
        self.path = path
        self.name = path
        self._is_file = is_file

    def path(self):  # pragma: no cover
        return self.path

    def is_file(self):
        return self._is_file


@patch("os.scandir")
def test_find_dotenv_files(mock_scandir):
    # Mock os.scandir() for files
    mock_scandir.return_value = [
        DirEntry(filename)
        for filename in ["test.py", "abba", "env", "test.env", ".env"]
    ]
    assert list(clean_dotenv._find_dotenv_files(None)) == ["test.env", ".env"]

    # Mock os.scandir() for directories
    mock_scandir.return_value = [
        DirEntry(filename, is_file=False)
        for filename in ["test.py", "abba", "env", "test.env", ".env", "env"]
    ]
    assert list(clean_dotenv._find_dotenv_files(None)) == []


@patch("dotenv.main.DotEnv")
def test_clean_env_function(mock_dotenv):
    dotenv_dict = {"KEY1": "secret_value1", "KEY2": "secret_value2"}
    mock_dotenv.return_value.dict.return_value.items.return_value = dotenv_dict.items()

    with patch("builtins.open", mock_open()) as mock_file:
        clean_dotenv._clean_env("test.env")
        mock_file.assert_called_with("test.env.example", "w")
        expected_calls = [call("KEY1="), call("\n"), call("KEY2="), call("\n")]
        mock_file.return_value.write.assert_has_calls(expected_calls)


def test_find_dotenv_files_function():
    with patch("os.scandir") as mock_scandir:
        mock_scandir.return_value = [DirEntry("test.env")]

        result = list(clean_dotenv._find_dotenv_files("path_to_root"))

        assert result == ["test.env"]


@patch("argparse.ArgumentParser.parse_args")
@patch("clean_dotenv._main")
def test_main(mock_main, mock_parse_args):
    mock_parse_args.return_value = MagicMock(root_path="test_rpath")

    clean_dotenv.main()

    mock_main.assert_called_once_with("test_rpath")


def test__main():
    # Mock _find_dotenv_files
    mm_find_dotenv = MagicMock(return_value=[".env", "test.env"])
    clean_dotenv._find_dotenv_files = mm_find_dotenv

    # Mock _clean_env
    mm_clean_env = MagicMock()
    clean_dotenv._clean_env = mm_clean_env

    # Call main method
    clean_dotenv._main("test_directory")

    # Detection should be called once
    mm_find_dotenv.assert_called_once_with("test_directory")

    # The creation of new .env file should be called twice, last with "test.env"
    assert mm_clean_env.call_count == 2
    mm_clean_env.assert_called_with("test.env")
