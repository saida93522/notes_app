from django.core import paginator
from django.http import response
from django.template import context
from django.test import TestCase

from django.urls import reverse
from django.contrib import auth
from django.contrib.auth import authenticate

import re
import datetime
from datetime import timezone
from django.utils import timezone as django_timezone
import pytz

from lmn.models import Note, Show, Venue
from django.contrib.auth.models import User


# TODO verify correct templates are rendered.

class TestEmptyViews(TestCase):

    """ Main views - the ones in the navigation menu """

    def test_with_no_artists_returns_empty_list(self):
        response = self.client.get(reverse('artist_list'))
        self.assertFalse(response.context['artists'])  # An empty list is false

    def test_with_no_venues_returns_empty_list(self):
        response = self.client.get(reverse('venue_list'))
        self.assertFalse(response.context['venues'])  # An empty list is false

    def test_with_no_notes_returns_empty_list(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertFalse(response.context['notes'])  # An empty list is false


class TestArtistViews(TestCase):

    fixtures = ['testing_artists', 'testing_venues', 'testing_shows']

    def test_all_artists_displays_all_alphabetically(self):
        response = self.client.get(reverse('artist_list'))

        # .* matches 0 or more of any character. Test to see if
        # these names are present, in the right order

        regex = '.*ACDC.*REM.*Yes.*'
        response_text = str(response.content)

        self.assertTrue(re.match(regex, response_text))
        self.assertEqual(len(response.context['artists']), 3)

    def test_artists_search_clear_link(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'ACDC'})

        # There is a 'clear' link on the page and, its url is the main venue page
        all_artists_url = reverse('artist_list')
        self.assertContains(response, all_artists_url)

    def test_artist_search_no_search_results(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'Queen'})
        self.assertNotContains(response, 'Yes')
        self.assertNotContains(response, 'REM')
        self.assertNotContains(response, 'ACDC')
        # Check the length of artists list is 0
        self.assertEqual(len(response.context['artists']), 0)

    def test_artist_search_partial_match_search_results(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'e'})
        # Should be two responses, Yes and REM
        self.assertContains(response, 'Yes')
        self.assertContains(response, 'REM')
        self.assertNotContains(response, 'ACDC')
        # Check the length of artists list is 2
        self.assertEqual(len(response.context['artists']), 2)

    def test_artist_search_one_search_result(self):
        response = self.client.get(reverse('artist_list'), {'search_name': 'ACDC'})
        self.assertNotContains(response, 'REM')
        self.assertNotContains(response, 'Yes')
        self.assertContains(response, 'ACDC')
        # Check the length of artists list is 1
        self.assertEqual(len(response.context['artists']), 1)

    def test_correct_template_used_for_artists(self):
        # Show all
        response = self.client.get(reverse('artist_list'))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')

        # Search with matches
        response = self.client.get(reverse('artist_list'), {'search_name': 'ACDC'})
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')
        # Search no matches
        response = self.client.get(reverse('artist_list'), {'search_name': 'Non Existant Band'})
        self.assertTemplateUsed(response, 'lmn/artists/artist_list.html')

        # Artist detail
        response = self.client.get(reverse('artist_detail', kwargs={'artist_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_detail.html')

        # Artist list for venue
        response = self.client.get(reverse('artists_at_venue', kwargs={'venue_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list_for_venue.html')

    def test_artist_detail(self):
        """ Artist 1 details displayed in correct template """
        # kwargs to fill in parts of url. Not get or post params

        response = self.client.get(reverse('artist_detail', kwargs={'artist_pk': 1}))
        self.assertContains(response, 'REM')
        self.assertEqual(response.context['artist'].name, 'REM')
        self.assertEqual(response.context['artist'].pk, 1)

    def test_get_artist_that_does_not_exist_returns_404(self):
        response = self.client.get(reverse('artist_detail', kwargs={'artist_pk': 10}))
        self.assertEqual(response.status_code, 404)

    def test_venues_played_at_most_recent_shows_first(self):
        # For each artist, display a list of venues they have played shows at.
        # Artist 1 (REM) has played at venue 2 (Turf Club) on two dates

        url = reverse('venues_for_artist', kwargs={'artist_pk': 1})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1, show2 = shows[0], shows[1]
        self.assertEqual(2, len(shows))

        self.assertEqual(show1.artist.name, 'REM')
        self.assertEqual(show1.venue.name, 'The Turf Club')

        # From the fixture, show 2's "show_date": "2017-02-02T19:30:00-06:00"
        expected_date = datetime.datetime(2017, 2, 2, 19, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # from the fixture, show 1's "show_date": "2017-01-02T17:30:00-00:00",
        self.assertEqual(show2.artist.name, 'REM')
        self.assertEqual(show2.venue.name, 'The Turf Club')
        expected_date = datetime.datetime(2017, 1, 2, 17, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show2.show_date, expected_date)

        # Artist 2 (ACDC) has played at venue 1 (First Ave)

        url = reverse('venues_for_artist', kwargs={'artist_pk': 2})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1 = shows[0]
        self.assertEqual(1, len(shows))

        # This show has "show_date": "2017-01-21T21:45:00-00:00",
        self.assertEqual(show1.artist.name, 'ACDC')
        self.assertEqual(show1.venue.name, 'First Avenue')
        expected_date = datetime.datetime(2017, 1, 21, 21, 45, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # Artist 3, no shows

        url = reverse('venues_for_artist', kwargs={'artist_pk': 3})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        self.assertEqual(0, len(shows))

    def test_no_links_to_notes_for_future_shows_by_artist(self):
        # set show 3 - with no notes - to one year from current date
        # show is artist 2, at venue 1
        show_future = Show.objects.get(pk=3)
        show_future.show_date = django_timezone.now() + datetime.timedelta(365)
        show_future.save()

        url = reverse('venues_for_artist', kwargs={'artist_pk': 2})
        response = self.client.get(url)
        show = response.context['shows'][0]
        self.assertFalse(show.in_past) # show is not in the past

        # verify user does not have link to make a note for this show or view show notes
        self.assertNotContains(response, 'See notes for this show')
        self.assertNotContains(response, 'Add a note')


class TestVenues(TestCase):

    fixtures = ['testing_venues', 'testing_artists', 'testing_shows']

    def test_with_venues_displays_all_alphabetically(self):
        response = self.client.get(reverse('venue_list'))

        # .* matches 0 or more of any character. Test to see if
        # these names are present, in the right order

        regex = '.*First Avenue.*Target Center.*The Turf Club.*'
        response_text = str(response.content)

        self.assertTrue(re.match(regex, response_text))

        self.assertEqual(len(response.context['venues']), 3)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_search_clear_link(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'Fine Line'})

        # There is a clear link, it's url is the main venue page
        all_venues_url = reverse('venue_list')
        self.assertContains(response, all_venues_url)

    def test_venue_search_no_search_results(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'Fine Line'})
        self.assertNotContains(response, 'First Avenue')
        self.assertNotContains(response, 'Turf Club')
        self.assertNotContains(response, 'Target Center')
        # Check the length of venues list is 0
        self.assertEqual(len(response.context['venues']), 0)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_search_partial_match_search_results(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'c'})
        # Should be two responses, Yes and REM
        self.assertNotContains(response, 'First Avenue')
        self.assertContains(response, 'Turf Club')
        self.assertContains(response, 'Target Center')
        # Check the length of venues list is 2
        self.assertEqual(len(response.context['venues']), 2)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_venue_search_one_search_result(self):
        response = self.client.get(reverse('venue_list'), {'search_name': 'Target'})
        self.assertNotContains(response, 'First Avenue')
        self.assertNotContains(response, 'Turf Club')
        self.assertContains(response, 'Target Center')
        # Check the length of venues list is 1
        self.assertEqual(len(response.context['venues']), 1)
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

    def test_all_venues_unknown_city_just_shows_state(self):
        # create venue with unknown city
        venue = Venue(name='Livestream', city='Unknown', state='Minnesota')
        venue.save()
        response = self.client.get(reverse('venue_list'))

        # 'Livestream' is second venue on page - listed in alphabetical order
        # check venue name and state on page
        self.assertContains(response, 'Livestream')
        self.assertEqual(response.context['venues'][1].name, 'Livestream')
        self.assertContains(response, 'Minnesota')
        self.assertEqual(response.context['venues'][1].state, 'Minnesota')

        # check venue city not on page despite having Unknown value in city
        self.assertNotContains(response, 'Unknown')
        self.assertEqual(response.context['venues'][1].city, 'Unknown')

    def test_venue_detail(self):
        # venue 1 details displayed in correct template
        # kwargs to fill in parts of url. Not get or post params
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 1}))
        self.assertContains(response, 'First Avenue')
        self.assertEqual(response.context['venue'].name, 'First Avenue')
        self.assertEqual(response.context['venue'].pk, 1)
        self.assertTemplateUsed(response, 'lmn/venues/venue_detail.html')

    def test_venue_detail_unknown_city_just_shows_state(self):
        # create venue with unknown city
        venue = Venue(name='Livestream', city='Unknown', state='Minnesota')
        venue.save()
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 4}))

        # check venue name and state on page
        self.assertContains(response, 'Livestream')
        self.assertEqual(response.context['venue'].name, 'Livestream')
        self.assertContains(response, 'Minnesota')
        self.assertEqual(response.context['venue'].state, 'Minnesota')

        # check venue city not on page despite having Unknown value in city
        self.assertNotContains(response, 'Unknown')
        self.assertEqual(response.context['venue'].city, 'Unknown')

    def test_get_venue_that_does_not_exist_returns_404(self):
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 10}))
        self.assertEqual(response.status_code, 404)

    def test_artists_played_at_venue_most_recent_first(self):
        # Artist 1 (REM) has played at venue 2 (Turf Club) on two dates

        url = reverse('artists_at_venue', kwargs={'venue_pk': 2})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1, show2 = shows[0], shows[1]
        self.assertEqual(2, len(shows))

        self.assertEqual(show1.artist.name, 'REM')
        self.assertEqual(show1.venue.name, 'The Turf Club')

        expected_date = datetime.datetime(2017, 2, 2, 19, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        self.assertEqual(show2.artist.name, 'REM')
        self.assertEqual(show2.venue.name, 'The Turf Club')
        expected_date = datetime.datetime(2017, 1, 2, 17, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(show2.show_date, expected_date)

        # Artist 2 (ACDC) has played at venue 1 (First Ave)

        url = reverse('artists_at_venue', kwargs={'venue_pk': 1})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        show1 = shows[0]
        self.assertEqual(1, len(shows))

        self.assertEqual(show1.artist.name, 'ACDC')
        self.assertEqual(show1.venue.name, 'First Avenue')
        expected_date = datetime.datetime(2017, 1, 21, 21, 45, 0, tzinfo=timezone.utc)
        self.assertEqual(show1.show_date, expected_date)

        # Venue 3 has not had any shows

        url = reverse('artists_at_venue', kwargs={'venue_pk': 3})
        response = self.client.get(url)
        shows = list(response.context['shows'].all())
        self.assertEqual(0, len(shows))

    def test_no_links_to_notes_for_future_shows_at_venue(self):
        # set show 3 - with no notes - to one year from current date
        # show is artist 2, at venue 1
        show_future = Show.objects.get(pk=3)
        show_future.show_date = django_timezone.now() + datetime.timedelta(365)
        show_future.save()

        url = reverse('artists_at_venue', kwargs={'venue_pk': 1})
        response = self.client.get(url)
        show = response.context['shows'][0]
        self.assertFalse(show.in_past) # show is not in the past

        # verify user does not have link to make a note for this show or view show notes
        self.assertNotContains(response, 'See notes for this show')
        self.assertNotContains(response, 'Add a note')

    def test_correct_template_used_for_venues(self):
        # Show all
        response = self.client.get(reverse('venue_list'))
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

        # Search with matches
        response = self.client.get(reverse('venue_list'), {'search_name': 'First'})
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

        # Search no matches
        response = self.client.get(reverse('venue_list'), {'search_name': 'Non Existant Venue'})
        self.assertTemplateUsed(response, 'lmn/venues/venue_list.html')

        # Venue detail
        response = self.client.get(reverse('venue_detail', kwargs={'venue_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/venues/venue_detail.html')

        response = self.client.get(reverse('artists_at_venue', kwargs={'venue_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/artists/artist_list_for_venue.html')


class TestAddNoteUnauthentictedUser(TestCase):
    # Have to add artists and venues because of foreign key constrains in show
    fixtures = ['testing_artists', 'testing_venues', 'testing_shows'] 

    def test_add_note_unauthenticated_user_redirects_to_login(self):
        response = self.client.get('/notes/add/1/', follow=True)  # Use reverse() if you can, but not required.
        # Should redirect to login; which will then redirect to the notes/add/1 page on success.
        self.assertRedirects(response, '/accounts/login/?next=/notes/add/1/')


class TestAddNotesWhenUserLoggedIn(TestCase):

    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']

    def setUp(self):
        user = User.objects.first()
        self.client.force_login(user)

    def test_save_note_for_non_existent_show_is_error(self):
        new_note_url = reverse('new_note', kwargs={'show_pk': 100})
        response = self.client.post(new_note_url)
        self.assertEqual(response.status_code, 404)

    def test_can_save_new_note_for_show_blank_data_is_error(self):
        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk': 1})

        # No post params
        response = self.client.post(new_note_url, follow=True)
        # No note saved, should show same page
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # no title
        response = self.client.post(new_note_url, {'text': 'blah blah'}, follow=True)
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # no text
        response = self.client.post(new_note_url, {'title': 'blah blah'}, follow=True)
        self.assertTemplateUsed('lmn/notes/new_note.html')

        # nothing added to database
        # 2 test notes provided in fixture, should still be 2
        self.assertEqual(Note.objects.count(), initial_note_count)   

    def test_add_note_database_updated_correctly(self):
        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk': 3})

        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'}, 
            follow=True)

        # Verify note is in database
        new_note_query = Note.objects.filter(text='ok', title='blah blah')
        self.assertEqual(new_note_query.count(), 1)

        # And one more note in DB than before
        self.assertEqual(Note.objects.count(), initial_note_count + 1)

        # Date correct?
        now = django_timezone.now() # timezone matches db timezone
        posted_date = new_note_query.first().posted_date
        self.assertEqual(now.date(), posted_date.date())

        # there is a slight second delay for saving to db - so am only checking correct hour and minute
        # Hour correct?
        self.assertEqual(now.time().hour, posted_date.time().hour) 
        # Minute correct?
        self.assertEqual(now.time().minute, posted_date.time().minute)

    def test_redirect_to_note_detail_after_save(self):
        new_note_url = reverse('new_note', kwargs={'show_pk': 3})
        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'}, 
            follow=True)

        new_note = Note.objects.filter(text='ok', title='blah blah').first()

        self.assertRedirects(response, reverse('note_detail', kwargs={'note_pk': new_note.pk}))
        
    def test_save_note_same_user_same_show_is_error(self):
        initial_note_count = Note.objects.count()

        # show 1 already has a note from this user
        new_note_url = reverse('new_note', kwargs={'show_pk': 1})
        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'},)

        # No note saved, should show the detail page for the note that is already in the db
        self.assertTemplateUsed('lmn/notes/note_detail.html')

        # error message shown to user
        messages = response.context['messages']
        message_text = [ message.message for message in messages ] 
        self.assertIn('You already created a note for this show.', message_text)

        # nothing added to database
        # 2 test notes provided in fixture, should still be 2
        self.assertEqual(Note.objects.count(), initial_note_count)


class TestAddNotesFutureShows:

    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']

    def setUp(self):
        user = User.objects.first()
        self.client.force_login(user)
        self.change_show_dates()

    def change_show_dates(self):
        show_future = Show.objects.get(pk=1)
        # set show 1 to one year from current date
        show_future.show_date = django_timezone.now() + datetime.timedelta(365)
        show_future.save()

        show_present = Show.objects.get(pk=2)
        # set show 2 to current time and date
        show_present.show_date = django_timezone.now()
        show_present.save()

        show_recent = Show.objects.get(pk=3)
        # set show 3 to one second before current time and date
        show_recent.show_date = django_timezone.now() - datetime.timedelta(seconds=1)
        show_recent.save()

    def test_can_save_new_note_for_current_show_is_error(self):
        # show date and time is same as current server date and time
        initial_note_count = Note.objects.count()

        # change show dates again to ensure show 2 has most recent current time for test
        self.change_show_dates()

        new_note_url = reverse('new_note', kwargs={'show_pk': 2})
        response = self.client.post(new_note_url, follow=True)

        # No note saved, should redirect back to note_list page
        self.assertTemplateUsed('lmn/notes/note_list.html')
        self.assertRedirects(response, reverse('notes_for_show', kwargs={'show_pk': 2}))

        # correct error message is added
        messages = response.context['messages']
        message_text = [ message.message for message in messages]
        self.assertIn('Cannot create a note for a show that has not happened yet.', message_text)

        # nothing added to database
        # 2 test notes provided in fixture, should still be 2
        self.assertEqual(Note.objects.count(), initial_note_count)

    def test_can_save_new_note_for_future_show_is_error(self):
        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk': 1})
        response = self.client.post(new_note_url, follow=True)

        # No note saved, should redirect back to note_list page
        self.assertTemplateUsed('lmn/notes/note_list.html')
        self.assertRedirects(response, reverse('notes_for_show', kwargs={'show_pk': 1}))

        # correct error message is added
        messages = response.context['messages']
        message_text = [ message.message for message in messages]
        self.assertIn('Cannot create a note for a show that has not happened yet.', message_text)

        # nothing added to database
        # 2 test notes provided in fixture, should still be 2
        self.assertEqual(Note.objects.count(), initial_note_count)

    def test_add_note_database_updated_correctly_very_recent_show(self):
        # show date and time is less than 1 minute ago
        initial_note_count = Note.objects.count()

        new_note_url = reverse('new_note', kwargs={'show_pk': 3})

        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'}, 
            follow=True)

        # Verify note is in database
        new_note_query = Note.objects.filter(text='ok', title='blah blah')
        self.assertEqual(new_note_query.count(), 1)

        # And one more note in DB than before
        self.assertEqual(Note.objects.count(), initial_note_count + 1)

        # Date correct?
        now = datetime.datetime.today()
        posted_date = new_note_query.first().posted_date
        self.assertEqual(now.date(), posted_date.date())  # TODO check time too

    def test_redirect_to_note_detail_after_save_very_recent_show(self):
        # show date and time is less than 1 minute ago
        new_note_url = reverse('new_note', kwargs={'show_pk': 3})
        response = self.client.post(
            new_note_url, 
            {'text': 'ok', 'title': 'blah blah'}, 
            follow=True)

        new_note = Note.objects.filter(text='ok', title='blah blah').first()

        self.assertRedirects(response, reverse('note_detail', kwargs={'note_pk': new_note.pk}))


class TestUserProfile(TestCase):
    # Have to add artists and venues because of foreign key constrains in show
    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 

    # verify correct list of reviews for a user
    def test_user_profile_show_list_of_their_notes(self):
        # get user profile for user 2. Should have 2 reviews for show 1 and 2.
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 2}))
        notes_expected = list(Note.objects.filter(user=2).order_by('-posted_date'))
        notes_provided = list(response.context['notes'])
        self.assertTemplateUsed('lmn/users/user_profile.html')
        self.assertEqual(notes_expected, notes_provided)

        # test notes are in date order, most recent first.
        # Note PK 3 should be first, then PK 2
        first_note = response.context['notes'][0]
        self.assertEqual(first_note.pk, 3)

        second_note = response.context['notes'][1]
        self.assertEqual(second_note.pk, 2)

    def test_user_with_no_notes(self):
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 3}))
        self.assertFalse(response.context['notes'])

    def test_username_shown_on_profile_page(self):
        # A string "username's notes" is visible
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 1}))
        self.assertContains(response, 'alice\'s notes')

        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 2}))
        self.assertContains(response, 'bob\'s notes')

    def test_correct_user_name_shown_different_profiles(self):
        logged_in_user = User.objects.get(pk=2)
        self.client.force_login(logged_in_user)  # bob
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 2}),follow=True)
        self.assertEqual((response.context['user']), logged_in_user)
        self.assertContains(response, 'Hi, bob')
        
        # Same message on another user's profile. Should still see logged in message 
        # for currently logged in user, in this case, bob
        response = self.client.get(reverse('user_profile', kwargs={'user_pk': 3}))
        self.assertEqual((response.context['user']), logged_in_user)
        self.assertContains(response, 'Hi, bob')

    def test_user_edit_own_profile(self):
        logged_in_user = User.objects.get(pk=1)
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('user_profile', kwargs={'user_pk':1}))
        # only logged in user should see edit profile link
        if logged_in_user.username == User.username:
            self.assertContains(response,'Edit profile')
            self.assertRedirects(response,'/user/profile/')
            
        response = self.client.post(reverse('user_profile', kwargs={'user_pk': 2}),follow=True)
        # other users should not see edit profile link
        if logged_in_user.username != User.username:
            self.assertNotContains(response,'Edit profile')

    def test_correct_template_used_for_update_profile(self):
        #other users profile and not logged in users
        response = self.client.get(reverse('my_user_profile'))
        self.assertTemplateNotUsed(response, 'lmn/users/update_profile.html')
        
        logged_in_user = User.objects.get(pk=1)
        self.client.force_login(logged_in_user)
        response = self.client.get(reverse('my_user_profile'))
        self.assertTemplateUsed(response, 'lmn/users/update_profile.html')


class TestNotes(TestCase):
    # Have to add Notes and Users and Show, and also artists and venues because of foreign key constraints in Show
    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 

    def test_latest_notes(self):
        response = self.client.get(reverse('latest_notes'))
        # Should be note 3, then 2, then 1
        context = response.context['notes']
        first, second, third = context[0], context[1], context[2]
        self.assertEqual(first.pk, 3)
        self.assertEqual(second.pk, 2)
        self.assertEqual(third.pk, 1)

    def test_notes_for_show_view(self):
        # Verify correct list of notes shown for a Show, most recent first
        # Show 1 has 2 notes with PK = 2 (most recent) and PK = 1
        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 1}))
        show = response.context['show']
        self.assertTrue(show.in_past) # show is in the past

        # verify user has link to make a new note 
        self.assertContains(response, 'Add your own notes for this show')
        self.assertNotContains(response, 'You can add a note once this show has started!')

        context = response.context['notes']
        first, second = context[0], context[1]
        self.assertEqual(first.pk, 2)
        self.assertEqual(second.pk, 1)

    def test_notes_for_show_view_with_future_show(self):
        # set show 3 - with no notes - to one year from current date
        show_future = Show.objects.get(pk=3)
        show_future.show_date = django_timezone.now() + datetime.timedelta(365)
        show_future.save()

        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 3}))
        show = response.context['show']
        self.assertFalse(show.in_past) # show is not in the past

        # verify user does not have link to make a note for this show
        self.assertContains(response, 'You can add a note once this show has started!')
        self.assertNotContains(response, 'Add your own notes for this show')

    def test_show_and_notes_displays_default_timezone_america_chicago(self):
        # Currently the default timezone is America/Chicago
        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 1}))

        # test show dates
        show = response.context['show']

        # context contains show data from db - in UTC
        # manually convert to America/Chicago for comparison to display date
        show_date_default_timezone = show.show_date.astimezone(pytz.timezone('America/Chicago'))
        show_date_default_timezone_display = show_date_default_timezone.strftime('%b. %d, %Y, %I:%M %p').replace(' 0', ' ').replace('AM', 'a.m.').replace('PM', 'p.m.')
        self.assertContains(response, show_date_default_timezone_display)

        # assert that the time in UTC is not displayed
        show_date_UTC = show.show_date
        show_date_UTC_display = show_date_UTC.strftime('%b. %d, %Y, %I:%M %p').replace(' 0', ' ').replace('AM', 'a.m.').replace('PM', 'p.m.')
        self.assertNotContains(response, show_date_UTC_display)

        # test note dates
        notes = response.context['notes']
        for note in notes:
            # context contains note data from db - in UTC
            # manually convert to America/Chicago for comparison to display dates
            note_date_default_timezone = note.posted_date.astimezone(pytz.timezone('America/Chicago'))
            note_date_default_timezone_display = note_date_default_timezone.strftime('%b. %d, %Y, %I:%M %p').replace(' 0', ' ').replace('AM', 'a.m.').replace('PM', 'p.m.')
            self.assertContains(response, note_date_default_timezone_display)

            # assert that the time in UTC is not displayed
            note_date_UTC = note.posted_date
            note_date_UTC_display = note_date_UTC.strftime('%b. %d, %Y, %I:%M %p').replace(' 0', ' ').replace('AM', 'a.m.').replace('PM', 'p.m.')
            self.assertNotContains(response, note_date_UTC_display)

    def test_notes_for_show_when_show_not_found(self):
        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 10000}))
        self.assertEqual(404, response.status_code)

    def test_correct_templates_uses_for_notes(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertTemplateUsed(response, 'lmn/notes/note_list.html')

        response = self.client.get(reverse('note_detail', kwargs={'note_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/notes/note_detail.html')

        response = self.client.get(reverse('notes_for_show', kwargs={'show_pk': 1}))
        self.assertTemplateUsed(response, 'lmn/notes/note_list.html')

        # Log someone in
        self.client.force_login(User.objects.first())
        response = self.client.get(reverse('new_note', kwargs={'show_pk': 3}))
        self.assertTemplateUsed(response, 'lmn/notes/new_note.html')


class TestUserAuthentication(TestCase):
    """ Some aspects of registration (e.g. missing data, duplicate username) covered in test_forms """
    """ Currently using much of Django's built-in login and registration system """
    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 
    
    def test_user_registration_logs_user_in(self):
        response = self.client.post(
            reverse('register'), 
            {
                'username': 'sam12345', 
                'email': 'sam@sam.com', 
                'password1': 'feRpj4w4pso3az', 
                'password2': 'feRpj4w4pso3az', 
                'first_name': 'sam', 
                'last_name': 'sam'
            }, 
            follow=True)

        # Assert user is logged in - one way to do it...
        user = auth.get_user(self.client)
        self.assertEqual(user.username, 'sam12345')

        # This works too. Don't need both tests, added this one for reference.
        # sam12345 = User.objects.filter(username='sam12345').first()
        # auth_user_id = int(self.client.session['_auth_user_id'])
        # self.assertEqual(auth_user_id, sam12345.pk)

    def test_user_registration_redirects_to_correct_page(self):
        # TODO If user is browsing site, then registers, once they have registered, they should
        # be redirected to the last page they were at, not the homepage.
        response = self.client.post(
            reverse('register'), 
            {
                'username': 'sam12345', 
                'email': 'sam@sam.com', 
                'password1': 'feRpj4w4pso3az@1!2', 
                'password2': 'feRpj4w4pso3az@1!2', 
                'first_name': 'sam', 
                'last_name': 'sam'
            }, 
            follow=True)
        new_user = authenticate(username='sam12345', password='feRpj4w4pso3az@1!2')
        self.assertRedirects(response, reverse('user_profile', kwargs={"user_pk": new_user.pk}))   
        self.assertContains(response, 'sam12345')  # page has user's username on it
        
        
class TestLogoutPage(TestCase):

    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']

    def test_logging_out_goes_to_logout_page(self):


        response = self.client.get(reverse('logout'))
        self.assertTemplateUsed('logout')

    def test_logout_page_redirects_to_homepage_after_logging_in(self):
        response = self.client.get(reverse('logout'))
        self.assertTemplateUsed('logout')
        response = self.client.get(reverse('login'))
        user = User.objects.first()
        self.client.force_login(user)
        self.assertTemplateUsed('homepage')

    def test_logging_in_from_a_page_not_logout_stays_on_page(self):
        response = self.client.get(reverse('latest_notes'))
        response = self.client.get(reverse('login'))
        user = User.objects.first()
        self.client.force_login(user)
        self.assertTemplateUsed('latest_notes')

        
class TestErrorViews(TestCase):

    def test_404_view(self):
        response = self.client.get('this isnt a url on the site')
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed('404.html')

    def test_404_view_note(self):
        # example view that uses the database, get note with ID 10000
        response = self.client.get(reverse('note_detail', kwargs={'note_pk': 1}))
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed('404.html')

    def test_403_view(self):
        # there are no current views that return 403. When users can edit notes, or edit 
        # their profiles, or do other activities when it must be verified that the 
        # correct user is signed in (else 403) then this test can be written.
        pass 


class TestLogoutPage(TestCase):

    fixtures = ['testing_users', 'testing_artists', 'testing_shows', 'testing_venues', 'testing_notes']

    def test_logging_out_goes_to_logout_page(self):
        response = self.client.get(reverse('logout'))
        self.assertTemplateUsed('logout')

    def test_logout_page_redirects_to_homepage_after_logging_in(self):
        response = self.client.get(reverse('logout'))
        self.assertTemplateUsed('logout')
        response = self.client.get(reverse('login'))
        user = User.objects.first()
        self.client.force_login(user)
        self.assertTemplateUsed('homepage')

    def test_logging_in_from_a_page_not_logout_stays_on_page(self):
        response = self.client.get(reverse('latest_notes'))
        response = self.client.get(reverse('login'))
        user = User.objects.first()
        self.client.force_login(user)
        self.assertTemplateUsed('latest_notes')

class TestPaginationLessThan11Users(TestCase):
    fixtures = ['testing_artists'] 

    # from https://stackoverflow.com/questions/58964496/django-test-pagination-emptypage
    def test_arists_page_starts_on_page_1(self):
        response = self.client.get(reverse('artist_list'))
        self.assertEquals(response.context['artists'].number, response.context['artists'].paginator.page(1).number)

    def test_venues_page_starts_on_page_1(self):
        response = self.client.get(reverse('venue_list'))
        self.assertEquals(response.context['venues'].number, response.context['venues'].paginator.page(1).number)

    def test_notes_page_starts_on_page_1(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertEquals(response.context['notes'].number, response.context['notes'].paginator.page(1).number)
    
    def test_no_more_pages_if_less_than_11_artists_in_database(self):
        response = self.client.get(reverse('artist_list'))
        self.assertFalse(response.context['artists'].has_next())
        self.assertFalse(response.context['artists'].has_previous())
    

class TestPaginationArtistPageMoreThanTenUsers(TestCase):
    fixtures = ['testing_many_artists']
    def test_more_than_1_page_if_more_than_11_artists_in_list(self):
        response = self.client.get(reverse('artist_list'))
        self.assertTrue(response.context['artists'].has_next())

    def test_arists_has_10_items_per_page(self):
        response = self.client.get(reverse('artist_list'))
        self.assertEquals(len(response.context['artists']), 10)
    
    def test_2_pages_for_artists_if_more_than_11_less_than_21(self):
        response = self.client.get(reverse('artist_list'))
        self.assertEquals(response.context['artists'].paginator.num_pages, 2)

    def test_artist_page_more_than_11_users_starts_on_page_1(self):
        response = self.client.get(reverse('artist_list'))
        self.assertEquals(response.context['artists'].number, response.context['artists'].paginator.page(1).number)
        self.assertNotEquals(response.context['artists'].number, response.context['artists'].paginator.page(2).number)
        
    def test_first_ten_artists_are_on_first_page(self):
        response = self.client.get(reverse('artist_list'))
        # gets first page
        page_one = response.context['artists'].paginator.get_page(1)

        # gets a list of the page object's values returns a query set
        # there are ten items in the object for 10 artisists in the list on page
        # arranged alphabetically starting with capitolized first
        page_one_list = page_one.paginator.object_list.values()

        # from https://stackoverflow.com/questions/59199820/typeerror-dict-values-object-is-not-subscriptable?noredirect=1&lq=1
        # puts dict_values object in a list so I can access the elements in it
        # page_one_list[0].values() returns a dict_values obj with the artist in the 0 position of the list
        aritst_0__dict = list(page_one_list[0].values())
        # accessing the [1] item in the list, the artist
        artist_in_position_0 = aritst_0__dict[1]
        self.assertEquals(artist_in_position_0, 'ACDC')
        
        aritst_1__dict = list(page_one_list[1].values())
        artist_in_position_1 = aritst_1__dict[1]
        self.assertEquals(artist_in_position_1, 'REM')
    
class TestPaginationVenuesPageMoreThanTenUsers(TestCase):
    fixtures = ['testing_many_venues']

    def test_more_than_1_page_if_more_than_11_venues_in_list(self):
        response = self.client.get(reverse('venue_list'))
        self.assertTrue(response.context['venues'].has_next())

    def test_venues_has_10_items_per_page(self):
        response = self.client.get(reverse('venue_list'))
        self.assertEquals(len(response.context['venues']), 10)
    
    def test_2_pages_for_venues_if_more_than_11_less_than_21(self):
        response = self.client.get(reverse('venue_list'))
        self.assertEquals(response.context['venues'].paginator.num_pages, 2)

    def test_venues_page_more_than_11_users_starts_on_page_1(self):
        response = self.client.get(reverse('venue_list'))
        self.assertEquals(response.context['venues'].number, response.context['venues'].paginator.page(1).number)
        self.assertNotEquals(response.context['venues'].number, response.context['venues'].paginator.page(2).number)

    def test_first_ten_venues_are_on_first_page(self):
        response = self.client.get(reverse('venue_list'))
        page_one = response.context['venues'].paginator.get_page(1)
        page_one_list = page_one.paginator.object_list.values()
        venue_0_dict = list(page_one_list[0].values())
        venue_in_position_0 = venue_0_dict[1]
        # arranged alphabetically
        self.assertEquals(venue_in_position_0, 'Excel energy center')
        

class TestPaginationNotesPageMoreThanTenUsers(TestCase):
    fixtures = ['testing_many_notes', 'testing_many_users', 'testing_shows', 'testing_venues', 'testing_artists']

    def test_more_than_1_page_if_more_than_11_notes_in_list(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertTrue(response.context['notes'].has_next())

    def test_notes_has_10_items_per_page(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertEquals(len(response.context['notes']), 10)
    
    def test_2_pages_for_notes_if_more_than_11_less_than_21(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertEquals(response.context['notes'].paginator.num_pages, 2)

    def test_notes_page_more_than_11_users_starts_on_page_1(self):
        response = self.client.get(reverse('latest_notes'))
        self.assertEquals(response.context['notes'].number, response.context['notes'].paginator.page(1).number)
        self.assertNotEquals(response.context['notes'].number, response.context['notes'].paginator.page(2).number)

