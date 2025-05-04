from django.shortcuts import render

def videocall(request):
    return render(request, 'videocall/videocall.html')
