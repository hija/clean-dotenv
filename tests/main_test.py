from os import DirEntry
from unittest.mock import MagicMock, call, mock_open, patch
import pytest
from clean_dotenv import _main as clean_dotenv
import tempfile
import shutil


class DirEntry:
    def __init__(self, path, is_file=True):
        self.path = path
        self.name = path
        self._is_file = is_file

    def path(self):  # pragma: no cover
        return self.path

    def is_file(self):
        return self._is_file


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("#test", "#test", id="comment-only"),
        pytest.param(
            "export AWS_PROFILE='test' #exporttest",
            "export AWS_PROFILE='' #exporttest",
            id="export",
        ),
        pytest.param(
            'AWS_PROFILE="test" #double',
            'AWS_PROFILE="" #double',
            id="double quotes",
        ),
        pytest.param(
            """
            AWS_PROFILE="123"
            AWS_KEY="123"
        """,
            """
            AWS_PROFILE=""
            AWS_KEY=""
        """,
            id="multiple",
        ),
        pytest.param(
            """
            AWS_PROFILE="123
            34"
            AWS_KEY="123"
        """,
            """
            AWS_PROFILE=""
            AWS_KEY=""
        """,
            id="multiline",
        ),
        pytest.param(
            """
            A="123"
            B='456'
        """,
            """
            A=""
            B=''
        """,
            id="mixed separator",
        ),
        pytest.param(
            """# Copy and paste the credentials here.
                #
                # Restart running containers whenever these values are updated.

                AWS_PROFILE="default"

                # Alternatively, if you wish to use keys directly, uncomment the 
                # following lines and provide the values. Comment out or remove the 
                # AWS_PROFILE line above.

                # AWS_ACCESS_KEY_ID=""
                # AWS_SECRET_ACCESS_KEY=""
                # AWS_SESSION_TOKEN=""
                """,
            """# Copy and paste the credentials here.
                #
                # Restart running containers whenever these values are updated.

                AWS_PROFILE=""

                # Alternatively, if you wish to use keys directly, uncomment the 
                # following lines and provide the values. Comment out or remove the 
                # AWS_PROFILE line above.

                # AWS_ACCESS_KEY_ID=""
                # AWS_SECRET_ACCESS_KEY=""
                # AWS_SESSION_TOKEN=""
                """,
            id="GitHub Issue #3 Example",
        ),
    ),
)
def test_clean_function(s, expected):
    # First we create a temp directory in which we store the .env file
    tmpdir = tempfile.mkdtemp()
    # We write the content into a .env
    with open(f"{tmpdir}/.env", "w") as f:
        print(s, end="", file=f)
    clean_dotenv._clean_env(f"{tmpdir}/.env")
    # We now get the cleaned file
    with open(f"{tmpdir}/.env.example", "r") as f:
        output = f.read()
    shutil.rmtree(tmpdir)
    assert output == expected


@pytest.mark.parametrize(
    ("s", "expected", "keep"),
    (
        pytest.param(
            "export AWS_PROFILE='test' #exporttest",
            "export AWS_PROFILE='test' #exporttest",
            ["AWS_PROFILE"],
            id="single-keep",
        ),
        pytest.param(
            """
            AWS_PROFILE="123"
            AWS_KEY="123"
        """,
            """
            AWS_PROFILE="123"
            AWS_KEY="123"
        """,
            ["AWS_PROFILE", "AWS_KEY"],
            id="multi-keep",
        ),
        pytest.param(
            """
            AWS_PROFILE="123
            34"
            AWS_KEY="123"
        """,
            """
            AWS_PROFILE="123
            34"
            AWS_KEY="123"
        """,
            ["AWS_PROFILE", "AWS_KEY"],
            id="multi-keep",
        ),
        pytest.param(
            """
            AWS_PROFILE="123"
            AWS_KEY="123"
        """,
            """
            AWS_PROFILE=""
            AWS_KEY="123"
        """,
            ["aws_profile", "AWS_KEY"],
            id="case-sensitive",
        ),
        pytest.param(
            """
            password=pa55w0rd
            url=www.google.com
        """,
            """
            password=
            url=www.google.com
        """,
            ["url"],
            id="GitHub Issue #5 Example",
        ),
    ),
)
def test_clean_function_with_values_to_keep(s, expected, keep):
    # First we create a temp directory in which we store the .env file
    tmpdir = tempfile.mkdtemp()
    # We write the content into a .env
    with open(f"{tmpdir}/.env", "w") as f:
        print(s, end="", file=f)
    clean_dotenv._clean_env(f"{tmpdir}/.env", values_to_keep=keep)
    # We now get the cleaned file
    with open(f"{tmpdir}/.env.example", "r") as f:
        output = f.read()
    shutil.rmtree(tmpdir)
    assert output == expected


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


def test_find_dotenv_files_function():
    with patch("os.scandir") as mock_scandir:
        mock_scandir.return_value = [DirEntry("test.env")]

        result = list(clean_dotenv._find_dotenv_files("path_to_root"))

        assert result == ["test.env"]


@patch("argparse.ArgumentParser.parse_args")
@patch("clean_dotenv._main._main")
def test_main(mock_main, mock_parse_args):
    mock_parse_args.return_value = MagicMock(root_path="test_rpath", keep=[])

    clean_dotenv.main()

    mock_main.assert_called_once_with(path_to_root="test_rpath", values_to_keep=[])


def test__main():
    # Mock _find_dotenv_files
    mm_find_dotenv = MagicMock(return_value=[".env", "test.env"])
    clean_dotenv._find_dotenv_files = mm_find_dotenv

    # Mock _clean_env
    mm_clean_env = MagicMock()
    clean_dotenv._clean_env = mm_clean_env

    # Call main method
    clean_dotenv._main(path_to_root="test_directory", values_to_keep=[])

    # Detection should be called once
    mm_find_dotenv.assert_called_once_with("test_directory")

    # The creation of new .env file should be called twice, last with "test.env"
    assert mm_clean_env.call_count == 2
    mm_clean_env.assert_called_with(path_to_env="test.env", values_to_keep=[])
