from django.contrib.auth import login
from django.shortcuts import redirect, render

from apps.accounts.forms import PublicUserCreationForm


def register(request):
    if request.method == "POST":
        form = PublicUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after registration
            login(request, user)
            return redirect("gate:index")
    else:
        form = PublicUserCreationForm()
    return render(request, "registration/register.html", {"form": form})
