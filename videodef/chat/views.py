from django.shortcuts import render

def chats(request):
    return render(request, "chats.html")
