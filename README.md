# GeoLocation Utility - glu.py
This utility takes 5-digit US zip codes or "City, State" values as input, looks
them up on [OpenWeatherMap's geocoding API](https://openweathermap.org/api/geocoding-api),
and displays the latitude and longitude coordinates of that location (or
locations if there is more than one municipality with that name).

Technical requirements:
* A recent version of Python 3
* An api key from [openweathermap.org](https://home.openweathermap.org/users/sign_up)

Also see `glu.py --help` for various options.
## Quick Start
```
git clone https://github.com/jarod-codes/geolocationutility.git
cd geolocationutility
pip install requests
set OPENWEATHER_APIKEY=yourapikey       # Windows cmd.exe
export OPENWEATHER_APIKEY=yourapikey    # Unix-y shell
python glu.py "Miami, FL" 10118 02108 98101
```
## Slow Start
This utility was written and tested on Windows 10 using cmd.exe and on 
Mac OS X using the Terminal default zsh. Both had the latest version of 
Python3 downloaded from the [Python downloads page](https://python.org/downloads).

If you are using something like Chocolatey or Homebrew to install Python, there
will probably be some slightly different configuring needed to get things going.

## Description
The motivations for writing this utility:
* Reinforce and expand my Python knowledge
* Demonstrate black-box, local testing by mocking external resources
* Demonstrate integration testing

## Developing
It's recommended to setup a Python virtual environment for testing. In
particular, the `test_glu_integrations.py` tests look in these locations
for python:
1. `venv/bin/python`
1. `venv\Scripts\python.exe`
1. `python` if one of the above two are not present. At this point, if
`python` is not in your `$PATH`, then the integration tests will fail.
```
git clone https://github.com/jarod-codes/geolocationutility.git
cd geolocationutility
python -m venv venv
source venv/bin/activate        # UNIX-y systems
venv\Scripts\activate.bat       # Windows cmd.exe
venv\Scripts\activate.ps1       # Windows PowerShell
pip install -r requirements.txt
```
Run only the local tests
```
pytest tests/test_glu.py
```
Run only the integration tests
```
touch ~/.openweather_apikey
echo yourapikey > ~/.openweather_apikey
pytest tests/test_glu_integration.py
```
Run all the tests with `pytest`
