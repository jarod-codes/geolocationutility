
import glu
import pytest
import re
import json
from unittest.mock import patch, mock_open

ARGV0 = "glu_test.py"
TESTAPIKEY = "abc123xyzzy"
COORDS1 = {"lat": "1.00", "lon": "-1.00"}

@pytest.fixture(scope="function")
def mock_get():
    mg = patch('requests.get')
    yield mg.start()
    mg.stop()

@pytest.fixture(scope="function")
def mock_file():
    mf = patch('builtins.open', mock_open(read_data=f'{TESTAPIKEY}\n'))
    yield mf.start()
    mf.stop()

# Tests improperly formatted locations
@patch("sys.argv", [ARGV0, "-k", f"key:{TESTAPIKEY}", "bad bad", "992291", "90210"])
def test_bad_location_inputs(capsys):
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "improperly formatted" in captured.err
    assert "bad bad" in captured.err
    assert "992291" in captured.err
    assert "90210" not in captured.err

# Tests default_environment_variable and UNKNOWN LOCATION
@patch.dict("os.environ", {"GLUTESTOPENWEATHERMAPAPIKEY": TESTAPIKEY})
@patch("glu.DEFAULT_ENV_VAR", "GLUTESTOPENWEATHERMAPAPIKEY")
@patch("sys.argv", [ARGV0, "City, ZZ"])
def test_default_env_unknown_location(mock_get, capsys):
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY
    table_row = r'\s*City, ZZ, US\s*UNKNOWN\s*LOCATION'
    assert re.search(table_row, captured.out)

# Tests default key file location
@patch.dict("os.environ", {"XXGLUTESTOPENWEATHERMAPAPIKEYXX": ""})
@patch("glu.DEFAULT_ENV_VAR", "XXGLUTESTOPENWEATHEMAPRAPIKEYXX")
@patch("sys.argv", [ARGV0, "10203"])
def test_default_key_file_unknown_zip(mock_get, mock_file, capsys):
    mock_get.return_value.json.return_value = {'cod': 404}
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY
    table_row = r'\s*10203\s*UNKNOWN\s*LOCATION'
    assert len(re.findall(table_row, captured.out)) == 1

# Tests --apikey key:123abc
@patch("sys.argv", [ARGV0, "-k", f"key:{TESTAPIKEY}", "City, ZZ"])
def test_apikey_key(mock_get):
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY

# Tests --apikey file:./testkeyfile
@patch("sys.argv", [ARGV0, "--apikey", "file:testkeyfile", "City, ZZ"])
def test_apikey_file(mock_get, mock_file):
    glu.main()
    mock_file.assert_called_once_with('testkeyfile')
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY

# Tests --apikey env:TEST_API_KEY_VAL
@patch.dict('os.environ', {'GLUPYTESTKEYVALUE': TESTAPIKEY})
@patch("sys.argv", [ARGV0, "--apikey", "env:GLUPYTESTKEYVALUE", "City, ZZ"])
def test_apikey_env(mock_get):
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY

# Tests --apikey key: 90210
@patch("sys.argv", [ARGV0, "-k", "key:", "90210"])
def test_apikey_key_empty(capsys):
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Unable to find key" in captured.err    

# Tests -k file 90210
@patch("sys.argv", [ARGV0, "-k", "file", "90210"])
def test_apikey_file_empty(capsys):
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Unable to parse --apikey parameter file" in captured.err    

# Tests --apikey nowhere:nothing 90210
@patch("sys.argv", [ARGV0, "-k", "nowhere:nothing", "90210"])
def test_apikey_bad_key_type(capsys):
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Unable to parse --apikey parameter" in captured.err    

@patch("sys.argv", [ARGV0, '-k', f'key:{TESTAPIKEY}', 'City One, ZZ', 'CityTwo,YY'])
def test_location_parsing_direct(mock_get, capsys):
    glu.main()
    captured = capsys.readouterr()
    assert mock_get.call_count == 2
    assert 'City One, ZZ, US' in captured.out
    assert 'CityTwo,YY, US' in captured.out

@patch("sys.argv", [ARGV0, '-k', f'key:{TESTAPIKEY}', 'New City, ZZ'])
def test_location_multiple_coords(mock_get, capsys):
    mock_get.return_value.json.return_value = [COORDS1, COORDS1, COORDS1]
    glu.main()
    captured = capsys.readouterr()
    assert len(re.findall(r'New City, ZZ, US', captured.out)) == 3

@patch("sys.argv", [ARGV0, '-k', f'key:{TESTAPIKEY}', '11111', '22222'])
def test_location_parsing_zip(mock_get, capsys):
    glu.main()
    captured = capsys.readouterr()
    assert mock_get.call_count == 2
    assert '11111' in captured.out
    assert '22222' in captured.out

@patch("sys.argv", [ARGV0, '-r', '-k', f'key:{TESTAPIKEY}', '   X Y Z  Z Y, X X, ZZ '])
def test_location_raw(mock_get):
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['q'] == '   X Y Z  Z Y, X X, ZZ '

@patch("sys.argv", [ARGV0, '-f', '-k', f'key:{TESTAPIKEY}', 'Xx, ZZ'])
def test_fullresponse_output(mock_get, capsys):
    mock_get.return_value.json.return_value = [COORDS1]
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert COORDS1 in json.loads(captured.out)
