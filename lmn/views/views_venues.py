from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from ..models import Venue, Show
from ..forms import VenueSearchForm


def venue_list(request):
    form = VenueSearchForm()
    search_name = request.GET.get('search_name')

    if search_name:
        # search for this venue, display results. Use case-insensitive contains
        venues = Venue.objects.filter(name__icontains=search_name).order_by('name')
    else:
        venues = Venue.objects.all().order_by('name')   # TODO paginate results

    return render(request, 'lmn/venues/venue_list.html', {'venues': venues, 'form': form, 'search_term': search_name})


def artists_at_venue(request, venue_pk):   # pk = venue_pk
    """ Get all of the artists who have played a show at the venue with pk provided """

    shows = Show.objects.filter(venue=venue_pk).order_by('-show_date') 
    venue = Venue.objects.get(pk=venue_pk)

    return render(request, 'lmn/artists/artist_list_for_venue.html', {'venue': venue, 'shows': shows})


def venue_detail(request, venue_pk):
    venue = get_object_or_404(Venue, pk=venue_pk)
    return render(request, 'lmn/venues/venue_detail.html', {'venue': venue})

# from https://simpleisbetterthancomplex.com/tutorial/2016/08/03/how-to-paginate-with-django.html
def venue_index(request):
    form = VenueSearchForm()
    search_name = request.GET.get('search_name')
    if search_name:
        venues = Venue.objects.filter(name__icontains=search_name).order_by('name')
    else:
        page = request.GET.get('page', 1)
        venue_list = Venue.objects.all().order_by('name')
        paginator = Paginator(venue_list, 10)
        try:
            venues = paginator.page(page)
        except PageNotAnInteger:
            venues = paginator.page(1)
        except EmptyPage:
            venues = paginator.page(paginator.num_pages)
    return render(request, 'lmn/venues/venue_list.html', {'venues': venues, 'form': form, 'search_term': search_name})