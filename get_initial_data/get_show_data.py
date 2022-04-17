from django.http.response import Http404
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

# URL to be used to find past shows
first_ave_url = 'https://first-avenue.com/shows/?orderby=past_shows'

# Known venues and their locations
venues_and_locations = {
    'Fine Line' : 'Minneapolis', 
    'Turf Club' : 'St. Paul', 
    'Palace Theatre' : 'St. Paul', 
    'The Fitzgerald Theater' : 'St. Paul', 
    'First Avenue' : 'Minneapolis',
    '7th St Entry' : 'St. Paul',
    }


def request_webpage_text(url):
    """Makes a request, and returns the html text of the webpage

    Args:
        url ([string]): url of the webpage

    Returns:
        [string]: html text of the webpage
    """
    response = requests.get('https://first-avenue.com/shows/?orderby=past_shows')
    if response.status_code == 404:
        return 404
    rtext = response.text
    return rtext


def parse_page_for_show_information(rtext):
    """Parse page for show information using beautiful soup

    Args:
        rtext (rtext): Raw html text from https://first-avenue.com/shows/?orderby=past_shows

    Returns:
        [show_list]: List of dictionaries, each representing a show
    """
    if rtext == Http404:
        return 404
    page = BeautifulSoup(rtext, 'html.parser')
    shows = page.select('.show_list_item')
    show_list = []
    for show in shows:
        show_data = {}
        show_data['month'] = show.find(class_='month').text.strip('\n\t')
        show_data['day'] = show.find(class_='day').text
        show_data['year'] = show.find(class_='year').text
        show_data['venue_name'] = show.find(class_='venue_name').text.strip('\n\t')
        show_data['artist_name'] = show.h4.a.text.replace(u'\xa0', u' ')
        show_data['venue_state'] = 'Minnesota'
        show_list.append(show_data)
    return show_list


def get_venue_cities(show_list):
    """Check venue name and see if it is in the dictionary of known venue locations.

    Args:
        show_list ([list]): List of dictionaries, each representing a show

    Returns:
        [show_list]: List of dictionaries, each representing a show, now with the key value pair of show_list['venue_city'] = venue_city
    """
    if show_list == 404:
        return 404
    for show in show_list:
        if show['venue_name'] in venues_and_locations:
            show['venue_city'] = venues_and_locations[show['venue_name']]
        else:
            show['venue_city'] = 'Unknown'
    return show_list


def convert_show_datetime(show_datetime):
    """Converts a naive datetime to an aware datetime in America/Central, then converts to UTC.
    
    Args:
        show_datetime ([datetime]): Naive datetime object created using information from first ave response
    
    Returns:
        show_datetime_UTC ([datetime]) Aware datetime object converted to UTC"""
    # https://pynative.com/python-timezone/
    show_datetime_aware = pytz.timezone('America/Chicago').localize(show_datetime) # convert to aware datetime in the same timezone used in show locations (MN)
    show_datetime_UTC = show_datetime_aware.astimezone(pytz.utc) # convert aware datetime to UTC time zone for DB storage
    return show_datetime_UTC


def make_datetime_objects(show_list):
    """Create datetime objects to replace show_list['month'], show_list['day'], show_list['year']

    Args:
        show_list ([list]): List of dictionaries, each representing a show
    """
    if show_list == 404:
        return 404
    months = { 'Jan' : 1, 'Feb' : 2, 'Mar' : 3, 'Apr' : 4, 'May' : 5, 'Jun' : 6, 'Jul' : 7, 'Aug' : 8, 'Sep' : 9, 'Oct' : 10, 'Nov' : 11, 'Dec' : 12}
    for show in show_list:
        show['month'] = months[show['month']]
        show_datetime = convert_show_datetime(datetime.datetime(int(show['year']), int(show['month']), int(show['day']), 19, 0)) #19 hours and 0 minutes into the given day - default time
        show['datetime'] = show_datetime
        del show['month']
        del show['day']
        del show['year']
    return show_list


def get_past_show_data():
    webpage = request_webpage_text(first_ave_url)
    if webpage == 404:
        return Http404('First Ave Not Found')
    show_list = parse_page_for_show_information(webpage)
    show_list_with_cities = get_venue_cities(show_list)
    show_list_with_datetimes = make_datetime_objects(show_list_with_cities)
    return show_list_with_datetimes
