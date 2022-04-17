from django.shortcuts import render


def user_logout(request):
    return render (request,'registration/user_logout.html')