""" Views related to creating and viewing Notes for shows. """

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from django.http import HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.contrib import messages

from ..models import Note, Show
from ..forms import NewNoteForm 


@login_required
def new_note(request, show_pk):
    """Create a new Note for a Show."""
    show = get_object_or_404(Show, pk=show_pk)

    current_date = timezone.now()
    if current_date < show.show_date:
        messages.warning(request, 'Cannot create a note for a show that has not happened yet.')
        return redirect('notes_for_show', show_pk=show_pk)

    user_note_already_created = Note.objects.filter(user=request.user, show=show).first()
    if user_note_already_created:
        messages.warning(request, 'You already created a note for this show.')
        return render(request, 'lmn/notes/note_detail.html', {'note': user_note_already_created})

    if request.method == 'POST':
        form = NewNoteForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # prevent error involving db recovery from exception during unit testing
                with transaction.atomic():
                    note = form.save(commit=False)
                    note.user = request.user
                    note.show = show
                    note.save()
                    return redirect('note_detail', note_pk=note.pk)
            except IntegrityError:
                messages.warning(request, 'Can\'t save note: you have already created a note for this show.')
            except ValidationError:
                # from the db save override method preventing notes for future shows
                messages.warning(request, 'Cannot create a note for a show that has not happened yet.')
    else:
        form = NewNoteForm()

    return render(request, 'lmn/notes/new_note.html', {'form': form, 'show': show})


@login_required
def edit_note(request, note_pk):
    """Edit existing Note"""
    note = get_object_or_404(Note, pk=note_pk)

    if note.user == request.user:

        if request.method == 'POST':
            form = NewNoteForm(request.POST, request.FILES, instance=note)

            if form.is_valid():
                note = form.save(commit=False)
                note.save()
                return redirect('note_detail', note_pk=note.pk)
            else:
                messages.info(request, 'Please double check that all fields are filled out correctly and uploaded images are valid.')
                form = NewNoteForm(instance=note)
                return render(request, 'lmn/notes/edit_note.html', {'form': form, 'note': note})

        else:
            form = NewNoteForm(instance=note)
            return render(request, 'lmn/notes/edit_note.html', {'form': form, 'note': note})

    else:
        return HttpResponseForbidden()


@login_required
def delete_note(request, note_pk):
    """Delete one Note"""
    note = get_object_or_404(Note, pk=note_pk)

    if note.user == request.user:
        note.delete()
        messages.info(request, 'Note deleted!')
        return redirect('latest_notes')
    else:
        return HttpResponseForbidden()


def latest_notes(request):
    """Get the 20 most recent Notes, ordered with most recent first."""
    notes = Note.objects.all().order_by('-posted_date')[:20]   # the 20 most recent notes
    return render(request, 'lmn/notes/note_list.html', {'notes': notes})


def notes_for_show(request, show_pk): 
    """Get Notes for one show, most recent first."""
    show = get_object_or_404(Show, pk=show_pk)  
    notes = Note.objects.filter(show=show_pk).order_by('-posted_date')
    return render(request, 'lmn/notes/note_list.html', {'show': show, 'notes': notes})


def note_detail(request, note_pk):
    """Display one Note."""
    note = get_object_or_404(Note, pk=note_pk)
    return render(request, 'lmn/notes/note_detail.html', {'note': note})


# from https://simpleisbetterthancomplex.com/tutorial/2016/08/03/how-to-paginate-with-django.html
def notes_index(request):
    notes_list = Note.objects.all().order_by('-posted_date')
    page = request.GET.get('page', 1)
    paginator = Paginator(notes_list, 10)
    try:
        notes = paginator.page(page)
    except PageNotAnInteger:
        notes = paginator.page(1)
    except EmptyPage:
        notes = paginator.page(paginator.num_pages)
    return render(request, 'lmn/notes/note_list.html', { 'notes': notes })

