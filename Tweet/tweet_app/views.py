from django.contrib import messages
from django.shortcuts import render
from .models import Tweet
from .forms import TweetForm, UserRegistrationsForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .utils import generate_otp, send_otp_email
import time
from django.urls import reverse
# from django.urls import reverse
from django.http import HttpResponseRedirect

# Create your views here.
#Create a tweet
@login_required
def tweet_create(request):
    if request.method == "POST":
        form=TweetForm(request.POST,request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('tweet_list')
    else:
        form = TweetForm()
    return render(request, "tweet_form.html",{'form':form})


# Like or unlike a tweet
@login_required
def tweet_like(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)
    
    if tweet.likes.filter(id=request.user.id).exists():
        tweet.likes.remove(request.user)
    else:
        tweet.likes.add(request.user)
    
    # ✅ If the request is from HTMX (the button), just render the button, not the whole page
    if request.headers.get('HX-Request'):
        return render(request, 'tweet_like_area.html', {'tweet': tweet})

    # Fallback for non-JS users
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('tweet_list')))


#All the tweets
def tweet_list(request):
    # Use select_related to join the User table
    tweets = Tweet.objects.select_related('user').all().order_by("-created_at")
    return render(request, 'tweet_list.html',{"tweets":tweets})


#singal tweets
def tweet_detail(request,tweet_id):
    tweet = get_object_or_404(Tweet, pk =tweet_id)
    return render(request ,'tweet_detail.html',{"tweet":tweet})


#Edit a tweet
@login_required
def tweet_edit(request,tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id, user = request.user)
    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES, instance=tweet)  
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect("tweet_list")
    else:
        form = TweetForm(instance=tweet)
    return render(request, "tweet_form.html",{'form':form})

#delete a tweet
@login_required
def tweet_delete(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id, user=request.user)

    if request.method == "POST":
        tweet.delete()
        return redirect("tweet_list")

    return render(request, "tweet_confirm_delete.html", {'tweet': tweet})


@login_required
def tweet_search(request):
    query = request.GET.get('search', '')
    message = None
    
    if query:
        tweets = Tweet.objects.filter(text__icontains=query)
        if not tweets.exists():
            message = "No tweets found matching your search."
    else:
        # If no query, show no results (or all tweets, your choice)
        tweets = Tweet.objects.none() # Or Tweet.objects.all()
        message = "Please enter a search term."

    return render(request, 'tweet_list.html', {
        'tweets': tweets,
        'message': message,
        'query': query  # Pass query back to show in search box
    })


#user registration with OTP verification
def register(request):
    if request.method == 'GET':
        return render(request, 'registration/register.html', {'form': UserRegistrationsForm()})

    if 'send_otp' in request.POST:
        return handle_registration_request(request)    
    elif 'verify_otp' in request.POST:
        return handle_otp_verification(request)
    elif 'resend_otp' in request.POST:
        return handle_resend_otp(request)
    return redirect('register')


def login_view(request):
    if request.method == 'POST':
        # 1. Bind the POST data to the form
        form = UserLoginForm(request.POST)
        
        # 2. Check if form is valid (e.g., is 'email' a valid email?)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # 3. Get username from email
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Invalid email or password.")
                return render(request, 'registration/login.html', {'form': form})

            # 4. Authenticate
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('tweet_list')
            else:
                messages.error(request, "Invalid email or password.")
                
        # 5. If form is invalid, render it again with errors
        return render(request, 'registration/login.html', {'form': form})
    
    else:
        # 6. For a GET request, show a new, blank form
        form = UserLoginForm()
        
    return render(request, 'registration/login.html', {'form': form})



# View any user's profile
def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    # Get all tweets by this specific user
    user_tweets = Tweet.objects.filter(user=user_obj).order_by("-created_at")
    
    return render(request, 'profile.html', {
        'profile_user': user_obj,
        'user_tweets': user_tweets
    })

# Edit your own profile
@login_required
def profile_edit(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile', username=request.user.username)

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'profile_edit.html', context)



# ------------All registeration helper functions with otp
def handle_registration_request(request):
    form = UserRegistrationsForm(request.POST)
    if not form.is_valid():
        return render(request, 'registration/register.html', {'form': form})

    # Data is valid (checks were moved to forms.py)
    otp = generate_otp()
    email = form.cleaned_data['email']

    # Save to session
    request.session['pending_reg'] = form.cleaned_data
    request.session['otp'] = otp
    request.session['otp_time'] = time.time()
    request.session['reg_email'] = email

    send_otp_email(email, otp)
    
    messages.info(request, f"OTP sent to {email}.")
    return render(request, 'registration/register.html', {'otp_phase': True, 'email': email})

def handle_otp_verification(request):
    # Retrieve session data
    saved_otp = request.session.get('otp')
    user_data = request.session.get('pending_reg')
    otp_time = request.session.get('otp_time')

    # 1. Check Session Validity
    if not all([saved_otp, user_data, otp_time]):
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    # 2. Check Time Expiry (120 seconds)
    if time.time() - otp_time > 120:
        messages.error(request, "OTP expired.")
        return render(request, 'registration/register.html', {
            'otp_phase': True, 
            'email': user_data['email']
        })

    # 3. Verify OTP
    if request.POST.get('otp') == saved_otp:
        User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password1']
        )
        # Flush session data specifically related to registration
        request.session.flush() 
        messages.success(request, "Registration successful!")
        return redirect('login')
    
    # 4. Invalid OTP
    messages.error(request, "Invalid OTP.")
    return render(request, 'registration/register.html', {
        'otp_phase': True, 
        'email': user_data['email']
    })

def handle_resend_otp(request):
    email = request.session.get('reg_email')
    if not email:
        return redirect('register')
        
    otp = generate_otp()
    request.session['otp'] = otp
    request.session['otp_time'] = time.time()
    
    send_otp_email(email, otp)
    messages.info(request, "New OTP sent.")
    
    return render(request, 'registration/register.html', {'otp_phase': True, 'email': email})