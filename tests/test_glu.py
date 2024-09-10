
import glu
import sys
import pytest
import re
from requests import HTTPError


def test_usage(capsys):
    sys.argv = ['glu.py']
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert "the following arguments are required: location" in captured.err

# Tests improperly formatted locations
#["bad bad", "992291", "90210"]
def test_bad_location_inputs(capsys):
    sys.argv = ["glu.py", "-k", "key:abc123", "bad bad", "992291", "90210"]
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "improperly formatted" in captured.err
    assert "bad bad" in captured.err
    assert "992291" in captured.err
    assert "90210" not in captured.err


def test_old_and_busted_1(mocker):
    spy = mocker.spy(glu, 'get_api_key')
    sys.argv = ["glu.py", "-k", "key:abc123", "City, ZZ"]
    with pytest.raises(HTTPError) as e:
        glu.main()
    assert spy.spy_return == 'abc123'

# Tests default_environment_variable and UNKNOWN LOCATION
def test_default_env_unknown_location(mocker, capsys):
    import os
    os.environ['OPENWEATHER_APIKEY'] = 'abc123'
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ["glu.py", "City, ZZ"]
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == 'abc123'
    table_row = r'\s*City, ZZ, US\s*UNKNOWN\s*LOCATION'
    assert re.search(table_row, captured.out)

# Tests default key file location
def test_default_key_file_unknown_zip(mocker, capsys):
    import os
    os.environ['OPENWEATHER_APIKEY'] = ''
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = {'code': 404}
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    mock_file = mocker.mock_open(read_data='abc123\n')
    mocker.patch("builtins.open", mock_file)
    sys.argv = ["glu.py", "10203"]
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == 'abc123'
    table_row = r'\s*10203\s*UNKNOWN\s*LOCATION'
    assert re.search(table_row, captured.out)

# Tests --apikey key:123abc
def test_apikey_key(mocker):
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ["glu.py", "-k", "key:abc123", "City, ZZ"]
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == 'abc123'

# Tests --apikey file:./testkeyfile
def test_apikey_file(mocker):
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    mock_file = mocker.mock_open(read_data='abc123\n')
    mocker.patch("builtins.open", mock_file)
    sys.argv = ["glu.py", "--apikey", "file:testkeyfile", "City, ZZ"]
    glu.main()
    mock_file.assert_called_once_with('testkeyfile')
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == 'abc123'

# Tests --apikey env:TEST_API_KEY_VAL
def test_apikey_env(mocker):
    import os
    os.environ['GLUPYTESTKEYVALUE'] = 'abc123'
    mock_get_response = mocker.MagicMock()
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ["glu.py", "--apikey", "env:GLUPYTESTKEYVALUE", "City, ZZ"]
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['appid'] == 'abc123'


# Tests --apikey key: 90210
def test_apikey_key_empty(capsys):
    sys.argv = ['glu.py', '-k', 'key:', '90210']
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Unable to find key" in captured.err    


# Tests -k file 90210
def test_apikey_file_empty(capsys):
    sys.argv = ['glu.py', '-k', 'file', '90210']
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Unable to parse --apikey parameter file" in captured.err    

# Tests --apikey nowhere:nothing 90210
def test_apikey_bad_key_type(capsys):
    sys.argv = ['glu.py', '-k', 'nowhere:nothing', '90210']
    with pytest.raises(SystemExit) as e:
        glu.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Unable to parse --apikey parameter" in captured.err    


def test_location_parsing_direct(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = [{'lat': '1.00', 'lon': '-1.00'}]
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ['glu.py', '-k', 'key:abc123', 'City One, ZZ', 'CityTwo,YY']
    glu.main()
    captured = capsys.readouterr()
    assert mock_get.call_count == 2
    assert 'City One, ZZ, US' in captured.out
    assert 'CityTwo,YY, US' in captured.out

def test_location_parsing_zip(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = {'lat': '1.00', 'lon': '-1.00'}
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ['glu.py', '-k', 'key:abc123', '11111', '22222']
    glu.main()
    captured = capsys.readouterr()
    assert mock_get.call_count == 2
    assert '11111' in captured.out
    assert '22222' in captured.out


def test_location_raw(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = [{'lat': '1.00', 'lon': '-1.00'}]
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ['glu.py', '-r', '-k', 'key:abc123', '   X Y Z  Z Y, X X, ZZ ']
    glu.main()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs['params']['q'] == '   X Y Z  Z Y, X X, ZZ '

def test_fullresponse_output(mocker, capsys):
    mock_get_response = mocker.MagicMock()
    mock_get_response.json.return_value = [{'lat': '1.00', 'lon': '-1.00'}]
    mock_get = mocker.patch('requests.get', return_value=mock_get_response)
    sys.argv = ['glu.py', '-f', '-k', 'key:abc123', 'Xx, ZZ']
    glu.main()
    captured = capsys.readouterr()
    mock_get.assert_called_once()
    assert "[{'lat': '1.00', 'lon': '-1.00'}]" in captured.out

