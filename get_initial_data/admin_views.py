from django.http.response import HttpResponseForbidden
from .get_show_data import get_past_show_data
from lmn.models import Venue, Artist, Show
from django.shortcuts import render
from django.db import IntegrityError
from django.db import transaction

import logging


def populate_db(request):

    # https://stackoverflow.com/questions/28345842/how-to-access-custom-http-request-headers-on-django-rest-framework#28345921
    cron_header = request.META.get('HTTP_X_APPENGINE_CRON')
    
    if request.user.is_superuser or cron_header:
        shows = get_past_show_data() # Mock this, return example data, assert the right stuff will end up in the database
        for show in shows:
            artist_name = show['artist_name']
            venue_name = show['venue_name']
            venue_state = show['venue_state']
            venue_city = show['venue_city']
            date = show['datetime']

            try:
                with transaction.atomic():
                    Venue(name=venue_name, city=venue_city, state=venue_state).save()
            except IntegrityError:
                logging.info('Venue is already in database')

            try:
                with transaction.atomic():
                        Artist(name=artist_name).save()
            except IntegrityError:
                logging.info('Artist is already in database')

            try:
                with transaction.atomic():
                    artist = Artist.objects.get(name=artist_name)
                    venue = Venue.objects.get(name=venue_name)
                    Show(show_date=date, artist=artist, venue=venue).save()
            except IntegrityError:
                logging.info('Artist is already in database')
        return render(request, 'lmn/home.html')
    else:
        return HttpResponseForbidden()
