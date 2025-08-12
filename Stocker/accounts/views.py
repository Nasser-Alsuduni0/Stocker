from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import SignUpForm

def signup(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "" 
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.filter(name="Employee").first()
            if group:
                user.groups.add(group)
            login(request, user)
            messages.success(request, "Welcome! Account created.")
            return redirect(next_url or "main:dashboard")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form, "next": next_url})



