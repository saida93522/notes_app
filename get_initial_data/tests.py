from django.http.response import Http404
from django.test import TestCase
from django.urls import reverse

from lmn.models import User
from .get_show_data import get_past_show_data, parse_page_for_show_information, get_venue_cities, make_datetime_objects

from unittest.mock import patch
import datetime
import os
import pytz 


class TestGetShowData(TestCase):

    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_get_past_show_data(self, mock_webpage_text):
        with open(os.path.join('get_initial_data', 'test_data', 'example_first_avenue_response.html'), 'r') as example_response_file:
            first_ave_response = example_response_file.read()

        mock_webpage_text.return_value = first_ave_response 

        past_show_data = get_past_show_data()

        expected_data = [
            {'venue_name': 'The Fitzgerald Theater', 'artist_name': 'City and Colour', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 12, 1, 19, 0)},
            {'venue_name': 'Turf Club', 'artist_name': 'Ben Noble', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 12, 1, 19, 0)}, 
            {'venue_name': '7th St Entry', 'artist_name': 'Sunset', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 12, 1, 19, 0)},
            {'venue_name': 'Turf Club', 'artist_name': 'Preoccupations and METZ', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 30, 19, 0)}, 
            {'venue_name': 'Fine Line', 'artist_name': 'The Aces', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis', 'datetime': datetime.datetime(2021, 11, 30, 19, 0)}, 
            {'venue_name': '7th St Entry', 'artist_name': 'glass beach', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 29, 19, 0)}, 
            {'venue_name': 'Turf Club', 'artist_name': 'Monophonics', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 28, 19, 0)}, 
            {'venue_name': 'First Avenue', 'artist_name': 'Beach Bunny', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis', 'datetime': datetime.datetime(2021, 11, 28, 19, 0)}, 
            {'venue_name': '7th St Entry', 'artist_name': 'Frozen Soul and Sanguisugabogg', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 28, 19, 0)}, 
            {'venue_name': 'First Avenue', 'artist_name': 'The Cactus Blossoms', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis', 'datetime': datetime.datetime(2021, 11, 27, 19, 0)}
        ]

        for show in expected_data:
            show_datetime = show['datetime']
            show_datetime_aware = pytz.timezone('America/Chicago').localize(show_datetime) # convert to aware datetime in the same timezone used in show locations (MN)
            show_datetime_UTC = show_datetime_aware.astimezone(pytz.utc) # convert aware datetime to UTC
            show['datetime'] = show_datetime_UTC
        

        self.assertEqual(past_show_data, expected_data)
    

    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_get_past_show_data_with_404(self, mock_webpage_text):

        mock_webpage_text.return_value = Http404 

        past_show_data = get_past_show_data()
        
        self.assertRaises(Http404)
        

    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_parse_page_for_show_information(self, mock_webpage_text):
        with open(os.path.join('get_initial_data', 'test_data', 'example_first_avenue_response.html'), 'r') as example_response_file:
            first_ave_response = example_response_file.read()

        mock_webpage_text.return_value = first_ave_response

        show_list = parse_page_for_show_information(first_ave_response)

        expected_parsed_data = [
            {'month': 'Dec', 'day': '1', 'year': '2021', 'venue_name': 'The Fitzgerald Theater', 'artist_name': 'City and Colour', 'venue_state': 'Minnesota'}, 
            {'month': 'Dec', 'day': '1', 'year': '2021', 'venue_name': 'Turf Club', 'artist_name': 'Ben Noble', 'venue_state': 'Minnesota'}, 
            {'month': 'Dec', 'day': '1', 'year': '2021', 'venue_name': '7th St Entry', 'artist_name': 'Sunset', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '30', 'year': '2021', 'venue_name': 'Turf Club', 'artist_name': 'Preoccupations and METZ', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '30', 'year': '2021', 'venue_name': 'Fine Line', 'artist_name': 'The Aces', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '29', 'year': '2021', 'venue_name': '7th St Entry', 'artist_name': 'glass beach', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '28', 'year': '2021', 'venue_name': 'Turf Club', 'artist_name': 'Monophonics', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '28', 'year': '2021', 'venue_name': 'First Avenue', 'artist_name': 'Beach Bunny', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '28', 'year': '2021', 'venue_name': '7th St Entry', 'artist_name': 'Frozen Soul and Sanguisugabogg', 'venue_state': 'Minnesota'}, 
            {'month': 'Nov', 'day': '27', 'year': '2021', 'venue_name': 'First Avenue', 'artist_name': 'The Cactus Blossoms', 'venue_state': 'Minnesota'}
        ]

        self.assertEqual(show_list, expected_parsed_data)


    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_parse_page_for_show_information_when_404(self, mock_webpage_text):
    

        mock_webpage_text.return_value = Http404

        show_list = parse_page_for_show_information(mock_webpage_text.return_value)

        self.assertRaises(Http404)


    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_get_venue_cities(self, mock_webpage_text):
        with open(os.path.join('get_initial_data', 'test_data', 'example_first_avenue_response.html'), 'r') as example_response_file:
            first_ave_response = example_response_file.read()

        mock_webpage_text.return_value = first_ave_response

        parsed_data = parse_page_for_show_information(first_ave_response)


        show_list_with_venue_cities = get_venue_cities(parsed_data)

        expected_parsed_data_with_cities = [
            {'month': 'Dec', 'day': '1', 'year': '2021', 'venue_name': 'The Fitzgerald Theater', 'artist_name': 'City and Colour', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Dec', 'day': '1', 'year': '2021', 'venue_name': 'Turf Club', 'artist_name': 'Ben Noble', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Dec', 'day': '1', 'year': '2021', 'venue_name': '7th St Entry', 'artist_name': 'Sunset', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Nov', 'day': '30', 'year': '2021', 'venue_name': 'Turf Club', 'artist_name': 'Preoccupations and METZ', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Nov', 'day': '30', 'year': '2021', 'venue_name': 'Fine Line', 'artist_name': 'The Aces', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis'}, 
            {'month': 'Nov', 'day': '29', 'year': '2021', 'venue_name': '7th St Entry', 'artist_name': 'glass beach', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Nov', 'day': '28', 'year': '2021', 'venue_name': 'Turf Club', 'artist_name': 'Monophonics', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Nov', 'day': '28', 'year': '2021', 'venue_name': 'First Avenue', 'artist_name': 'Beach Bunny', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis'}, 
            {'month': 'Nov', 'day': '28', 'year': '2021', 'venue_name': '7th St Entry', 'artist_name': 'Frozen Soul and Sanguisugabogg', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul'}, 
            {'month': 'Nov', 'day': '27', 'year': '2021', 'venue_name': 'First Avenue', 'artist_name': 'The Cactus Blossoms', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis'}
        ]

        self.assertEqual(show_list_with_venue_cities, expected_parsed_data_with_cities)


    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_get_venue_cities_when_404(self, mock_webpage_text):

        mock_webpage_text.return_value = Http404

        show_list = parse_page_for_show_information(mock_webpage_text.return_value)

        show_list_with_venue_cities = get_venue_cities(show_list)

        self.assertRaises(Http404)


    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_make_datetime_objects(self, mock_webpage_text):
        with open(os.path.join('get_initial_data', 'test_data', 'example_first_avenue_response.html'), 'r') as example_response_file:
            first_ave_response = example_response_file.read()

        mock_webpage_text.return_value = first_ave_response

        parsed_data = parse_page_for_show_information(first_ave_response)

        show_list_with_venue_cities = get_venue_cities(parsed_data)

        show_list_with_datetimes = make_datetime_objects(show_list_with_venue_cities)

        expected_parsed_data_with_datetimes = [
            {'venue_name': 'The Fitzgerald Theater', 'artist_name': 'City and Colour', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 12, 1, 19, 0)},
            {'venue_name': 'Turf Club', 'artist_name': 'Ben Noble', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 12, 1, 19, 0)}, 
            {'venue_name': '7th St Entry', 'artist_name': 'Sunset', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 12, 1, 19, 0)},
            {'venue_name': 'Turf Club', 'artist_name': 'Preoccupations and METZ', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 30, 19, 0)}, 
            {'venue_name': 'Fine Line', 'artist_name': 'The Aces', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis', 'datetime': datetime.datetime(2021, 11, 30, 19, 0)}, 
            {'venue_name': '7th St Entry', 'artist_name': 'glass beach', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 29, 19, 0)}, 
            {'venue_name': 'Turf Club', 'artist_name': 'Monophonics', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 28, 19, 0)}, 
            {'venue_name': 'First Avenue', 'artist_name': 'Beach Bunny', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis', 'datetime': datetime.datetime(2021, 11, 28, 19, 0)}, 
            {'venue_name': '7th St Entry', 'artist_name': 'Frozen Soul and Sanguisugabogg', 'venue_state': 'Minnesota', 'venue_city': 'St. Paul', 'datetime': datetime.datetime(2021, 11, 28, 19, 0)}, 
            {'venue_name': 'First Avenue', 'artist_name': 'The Cactus Blossoms', 'venue_state': 'Minnesota', 'venue_city': 'Minneapolis', 'datetime': datetime.datetime(2021, 11, 27, 19, 0)}
        ]
        
        for show in expected_parsed_data_with_datetimes:
            show_datetime = show['datetime']
            show_datetime_aware = pytz.timezone('America/Chicago').localize(show_datetime) # convert to aware datetime in the same timezone used in show locations (MN)
            show_datetime_UTC = show_datetime_aware.astimezone(pytz.utc) # convert aware datetime to UTC
            show['datetime'] = show_datetime_UTC

        self.assertEqual(show_list_with_datetimes, expected_parsed_data_with_datetimes)

    
    @patch('get_initial_data.get_show_data.request_webpage_text')
    def test_make_datetime_objects_with_404(self, mock_webpage_text):

        mock_webpage_text.return_value = Http404

        show_list = parse_page_for_show_information(mock_webpage_text.return_value)

        show_list_with_venue_cities = get_venue_cities(show_list)

        show_list_with_datetimes = make_datetime_objects(show_list_with_venue_cities)

        self.assertRaises(Http404)


class TestPopulateDatabaseWithUnauthorizedUser(TestCase):

    def test_unauthorized_user(self):
        response = self.client.get(reverse('populate_db'))
        self.assertEqual(response.status_code, 403)


class TestPopulateDatabaseWithAuthorizedUser(TestCase):


    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']


    def setUp(self):
        superuser = User.objects.create_user('test', 'test@test.com', 'password')
        superuser.is_superuser = True
        superuser.save()
        self.client.force_login(superuser)


    @patch('get_initial_data.admin_views.get_past_show_data', return_value=[])
    def test_authorized_user_can_populate_db(self, mock_data_from_first_ave):
        response = self.client.get(reverse('populate_db'))
        self.assertEqual(response.status_code, 200)

