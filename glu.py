#!/usr/bin/env python
import argparse
import requests
import json
import sys
import re
import os

DEFAULT_ENV_VAR = 'OPENWEATHER_APIKEY'
DEFAULT_KEY_PATH = '~/.openweather_apikey'
DEFAULT_PADDING = 20

class GluError(Exception):
    pass

def validate_locations(locations):
    city_state = r"^\w[\w|\s]*,\s*\w\w$"
    ZIP_CODE_LEN = 5
    valid = []
    invalid = []
    for location in locations:
        loc = location.strip()
        if (len(loc) == ZIP_CODE_LEN and loc.isdigit()):
            valid += [loc]
        elif re.match(city_state, loc):
            valid += [loc + ', US']
        else:
            invalid += [loc]
    return (valid, invalid)


def get_coords(locations, api_key):
    DEFAULT_TIMEOUT = 4.2
    location_coords = {}
    for location in locations:
        if location.isdigit():
            params = {'zip': location, 'appid': api_key}
            r = requests.get('https://api.openweathermap.org/geo/1.0/zip', params=params, timeout=DEFAULT_TIMEOUT)
            # If a zip code is invalid, openweathermap returns a 404.
            # To make things consistent with the {city},{state} lookup, 
            # don't raise a status code exception for a 404.
            if r.status_code != 404:
                r.raise_for_status()
            data = [r.json()]
        else:
            # The limit for free accounts appears to be 5, defaults to 1
            # otherwise.
            params = {"q": location, "limit": "5", "appid": api_key}
            # http://api.openweathermap.org/geo/1.0/direct?q={city name},{state code},{country code}&limit={limit}&appid={API key}
            r = requests.get('https://api.openweathermap.org/geo/1.0/direct', params=params, timeout=DEFAULT_TIMEOUT)
            # Unless a 200 status code is returned, raise an error
            r.raise_for_status()
            # If the location doesn't exist, openweathermap returns an empty
            # json array with a 200 status code.
            data = r.json()
            
        location_coords[f"{location}"] = data
    return location_coords


def get_api_key(maybe_api_key):
    if (maybe_api_key is not None):
        key_parts = maybe_api_key.split(':')
        if (len(key_parts) != 2):
            raise GluError(f'Unable to parse --apikey parameter {maybe_api_key}')
        match key_parts[0].lower():
            case 'key':
                if len(key_parts[1]) > 0:
                    return(key_parts[1])
                else:
                    raise GluError(f'Unable to find key in --apikey parameter {maybe_api_key}') 
            case 'env':
                return(os.environ[key_parts[1]])
            case 'file':
                with open(key_parts[1]) as f:
                    return(f.readline().strip())
            case _:
                raise GluError(f'Unable to parse --apikey parameter {maybe_api_key}')
    else:
        if (DEFAULT_ENV_VAR in os.environ and len(os.environ[DEFAULT_ENV_VAR]) > 0):
            return(os.environ[DEFAULT_ENV_VAR])
        try:
            with open(DEFAULT_KEY_PATH) as f:
                return(f.readline().strip())
        except FileNotFoundError:
            raise GluError(f'Could not find an API key for openweathermap.org\nTry setting {DEFAULT_ENV_VAR} environment variable')


def print_coords(coords, full_response):
    if (full_response):
        [print(json.dumps(v, indent=2)) for v in coords.values()]
    else:
        max_len = len(max(coords.keys(), key=len))
        max_len = max(max_len, len('LOCATION'))
        print(F"{'LOCATION':{max_len}} {'LATITUDE':>{DEFAULT_PADDING}} {'LONGITUDE':>{DEFAULT_PADDING}}")
        for k, v in coords.items():
            if ((len(v) < 1) or ('lat' not in v[0])):
                # Placeholder values for when the zip code or municipality don't
                # have coordinates.
                v = [{'lat': 'UNKNOWN', 'lon': 'LOCATION'}]
            for coord in v:
                print(f"{k:{max_len}} {coord['lat']:>{DEFAULT_PADDING}} {coord['lon']:>{DEFAULT_PADDING}}")

GLU_DESCRIPTION = \
'''
Geolocation Utility (glu.py) -
  Retrieve latitude and longitude values from the API at
  https://openweathermap.org/api/geocoding-api. Requires an API Key for
  authenticating the requests. Default locations for the API Key are
  the environment variable OPENWEATHER_APIKEY and, failing that, the first line
  of a UTF-8 text file ~/.openweather_apikey.
'''
GLU_EPILOG = \
"""
Example usage:
  The default is to search for a City, State or zip code in the U.S:
    python glu.py "Chicago, IL" "Pumpkin Center, NC" 10118 90210

  To search outside the U.S., use the -r flag:
    python glu.py -r "London, ON, CA"

  If multiple locations have the same name, openweathermap's API appears to
  limit the number of locations returned to 5.
    python glu.py -rf Union
"""
def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=GLU_DESCRIPTION, epilog=GLU_EPILOG)
    parser.add_argument('locations', action='extend', type=str, nargs='+', metavar='location', help='City, State or 5-digit zip code, US only')
    parser.add_argument('--apikey', '-k',  metavar="[key|env|file]:[value]", help="key:api_key_value OR env:key_environment_variable OR file:path_to_key_file")
    parser.add_argument('--raw', '-r', action='store_true', default=False, help="Pass on the location values directly to the openweathermap.org API")
    parser.add_argument('--fullresponse', '-f', action='store_true', default=False, help="Show the json body responses from openweathermap.org instead of the default table")
    args = parser.parse_args()

    try:
        api_key = get_api_key(args.apikey)
    except (GluError, FileNotFoundError) as e:
        print(f"{e}\n", file=sys.stderr)
        parser.print_usage()
        exit(1)
    except KeyError as e:
        print(f"Could not find environment variable {e}\n", file=sys.stderr)
        parser.print_usage()
        exit(1)

    if (args.raw):
        valid_locations = args.locations
    else:
        (valid_locations, invalid_locations) = validate_locations(args.locations)
        if (len(invalid_locations) > 0):
            print(f"These location names are improperly formatted:", file=sys.stderr)
            print(*invalid_locations, sep='\n', file=sys.stderr)
            exit(1)
    coords = get_coords(valid_locations, api_key)
    print_coords(coords, args.fullresponse)


if __name__ == "__main__":
    main()
