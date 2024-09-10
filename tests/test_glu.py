
import glu
import pytest
import re
import json
from unittest.mock import patch

ARGV0 = "glu_test.py"
TESTAPIKEY = "abc123xyzzy"
COORDS1 = {"lat": "1.00", "lon": "-1.00"}

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
def test_default_env_unknown_location(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY
    table_row = r'\s*City, ZZ, US\s*UNKNOWN\s*LOCATION'
    assert re.search(table_row, captured.out)

# Tests default key file location
@patch.dict("os.environ", {"XXGLUTESTOPENWEATHERMAPAPIKEYXX": ""})
@patch("glu.DEFAULT_ENV_VAR", "XXGLUTESTOPENWEATHEMAPRAPIKEYXX")
def test_default_key_file_unknown_zip(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = {'code': 404}
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    mock_file = mocker.mock_open(read_data=f'{TESTAPIKEY}\n')
    mocker.patch("builtins.open", mock_file)
    mocker.patch("sys.argv", [ARGV0, "10203"])
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY
    table_row = r'\s*10203\s*UNKNOWN\s*LOCATION'
    assert re.search(table_row, captured.out)

# Tests --apikey key:123abc
@patch("sys.argv", [ARGV0, "-k", f"key:{TESTAPIKEY}", "City, ZZ"])
def test_apikey_key(mocker):
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY

# Tests --apikey file:./testkeyfile
def test_apikey_file(mocker):
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    mock_file = mocker.mock_open(read_data=f'{TESTAPIKEY}\n')
    mocker.patch("builtins.open", mock_file)
    mocker.patch("sys.argv", [ARGV0, "--apikey", "file:testkeyfile", "City, ZZ"])
    glu.main()
    mock_file.assert_called_once_with('testkeyfile')
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == TESTAPIKEY

# Tests --apikey env:TEST_API_KEY_VAL
@patch.dict('os.environ', {'GLUPYTESTKEYVALUE': TESTAPIKEY})
@patch("sys.argv", [ARGV0, "--apikey", "env:GLUPYTESTKEYVALUE", "City, ZZ"])
def test_apikey_env(mocker):
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
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
def test_location_parsing_direct(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = [COORDS1]
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    glu.main()
    captured = capsys.readouterr()
    assert mock_get.call_count == 2
    assert 'City One, ZZ, US' in captured.out
    assert 'CityTwo,YY, US' in captured.out

@patch("sys.argv", [ARGV0, '-k', f'key:{TESTAPIKEY}', '11111', '22222'])
def test_location_parsing_zip(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = COORDS1
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    glu.main()
    captured = capsys.readouterr()
    assert mock_get.call_count == 2
    assert '11111' in captured.out
    assert '22222' in captured.out

@patch("sys.argv", [ARGV0, '-r', '-k', f'key:{TESTAPIKEY}', '   X Y Z  Z Y, X X, ZZ '])
def test_location_raw(mocker):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = [COORDS1]
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['q'] == '   X Y Z  Z Y, X X, ZZ '

@patch("sys.argv", [ARGV0, '-f', '-k', f'key:{TESTAPIKEY}', 'Xx, ZZ'])
def test_fullresponse_output(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = [COORDS1]
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert COORDS1 in json.loads(captured.out)
