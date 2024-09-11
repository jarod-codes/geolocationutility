
import pytest
import subprocess
import re
import os
import json

table_header = r'\s*LOCATION\s*LATITUDE\s*LONGITUDE'
table_coords = r'-?\d+\.\d+\s+-?\d+\.\d+'
table_unknown = r'UNKNOWN\s+LOCATION'
DEFAULT_ENV_VAR = 'OPENWEATHER_APIKEY'
DEFAULT_KEY_PATH = os.path.expanduser('~/.openweather_apikey')

if os.path.exists('venv/bin/python'):
    PYTHONENV = 'venv/bin/python'
elif os.path.exists('venv/Scripts/python.exe'):
    PYTHONENV = 'venv/Scripts/python'
else:
    PYTHONENV = 'python'

@pytest.fixture(scope="function")
def stop_on_prereqs_missing(request):
    yield
    if request.session.testsfailed > 0:
        pytest.exit("Stopping integration tests due to missing api key")

def test_prereqs(stop_on_prereqs_missing):
    env_key_present = DEFAULT_ENV_VAR in os.environ and \
        len(os.environ[DEFAULT_ENV_VAR]) > 0
    key_file_present = os.path.exists(DEFAULT_KEY_PATH)
    assert env_key_present or key_file_present, "To run the integration " \
        f"tests the default api key environment variable {DEFAULT_ENV_VAR} " \
        f"or the default key file {DEFAULT_KEY_PATH} is needed"

def test_us_locations():
    args = [PYTHONENV, 'glu.py', '90210', 'Chicago, IL']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 0
    output = glu.stdout.decode('utf-8')
    assert re.search(table_header, output)
    beverly_hills = r'\s*90210\s+' + table_coords
    assert re.search(beverly_hills, output)
    chicago = r'\s*Chicago, IL, US\s+' + table_coords
    assert re.search(chicago, output)
    
def test_unknown_locations():
    args = [PYTHONENV, 'glu.py', '90210', 'New XYZZY, ZZ']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 0
    output = glu.stdout.decode('utf-8')
    xyzzy = r'New XYZZY, ZZ, US\s+' + table_unknown
    assert re.search(xyzzy, output)

def test_global_location():
    args = [PYTHONENV, 'glu.py', '-r', 'Montreal, QC, CA']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 0
    output = glu.stdout.decode('utf-8')
    montreal = r'Montreal, QC, CA\s+' + table_coords
    assert re.search(montreal, output)

def test_same_us_location_names():
    args = [PYTHONENV, 'glu.py', 'Pumpkin Center, NC']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 0
    output = glu.stdout.decode('utf-8')
    pumpkin_center = r'Pumpkin Center, NC, US\s+' + table_coords
    assert len(re.findall(pumpkin_center, output)) == 3

def test_zip_not_found():
    args = [PYTHONENV, 'glu.py', '-f', '00000']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 0
    output = json.loads(glu.stdout)[0]
    assert output == {'cod': '404', 'message': 'not found'}

def test_us_location_not_found():
    args = [PYTHONENV, 'glu.py', '-f', 'New Xyzzyton, ZZ']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 0
    output = json.loads(glu.stdout)
    assert output == []

def test_bad_api_key():
    args = [PYTHONENV, 'glu.py', '-k', 'key:badkeyvalue', '-f', 'New York, NY']
    glu = subprocess.run(args, capture_output=True)
    assert glu.returncode == 1
    output = glu.stderr.decode('utf-8')
    assert 'does not like the api key badkeyvalue' in output
