import time
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from .models import Tweet
from .forms import TweetForm, UserRegistrationsForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import random
from django.core.mail import send_mail
import time

# Create your views here.

#All the tweets
def tweet_list(request):
    # Use select_related to join the User table
    tweets = Tweet.objects.select_related('user').all().order_by("-created_at")
    return render(request, 'tweet_list.html',{"tweets":tweets})


#singal tweets
def tweet_detail(request,tweet_id):
    tweet = get_object_or_404(Tweet, pk =tweet_id)
    return render(request ,'tweet_detail.html',{"tweet":tweet})

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

    #expiry time
    OTP_EXPIRY_SECONDS = 120
    if request.method == 'POST':
        
        # --- Phase 1: User submits basic info ---
        if 'send_otp' in request.POST:
            form = UserRegistrationsForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                username = form.cleaned_data['username']

                # Check if email or username already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, "An account with this email already exists.")
                    return render(request, 'registration/register.html', {'form': form})
                if User.objects.filter(username=username).exists():
                     messages.error(request, "This username is already taken.")
                     return render(request, 'registration/register.html', {'form': form})

                # Generate and send OTP
                otp = str(random.randint(100000, 999999))
                request.session['pending_registration'] = form.cleaned_data
                request.session['otp'] = otp
                request.session['otp_created_at'] = time.time()
                request.session['registration_email'] = email

                send_mail(
                    subject='Verify your email address for TweetApp',
                    message=f"""Hello { email },
                        Thank you for signing up with TweetApp — we’re excited to have you join our community!
                        To complete your registration and activate your account, please verify your email address.

                        Your one-time verification code (OTP) is:

                        { otp }

                        This code is valid for the next 5 minutes and can be used only once.
                        If you didn’t request this code, please ignore this email — your account will remain inactive until the code is verified.

                        Welcome aboard,
                        The TweetApp Team
                        support@tweetapp.com
                    """,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                )

                messages.info(request, f"An OTP has been sent to {email}. It will expire in 2 minutes.")
                return render(request, 'registration/register.html', {
                    'otp_phase': True,
                    'email': email
                })
            else:
                # Form is invalid, re-render with errors
                return render(request, 'registration/register.html', {'form': form})

        # --- Phase 2: User enters OTP to confirm ---
        elif 'verify_otp' in request.POST:
            entered_otp = request.POST.get('otp')
            saved_otp = request.session.get('otp')
            data = request.session.get('pending_registration')
            otp_created_at = request.session.get('otp_created_at')
            email = request.session.get('registration_email')

            if not all([saved_otp, data, otp_created_at, email]):
                messages.error(request, "Your session has expired. Please start over.")
                return redirect('register')

            # Check for expiry
            if (time.time() - otp_created_at) > OTP_EXPIRY_SECONDS:
                messages.error(request, "Your OTP has expired. Please request a new one.")
                return render(request, 'registration/register.html', {
                    'otp_phase': True,
                    'email': email
                })

            if entered_otp == saved_otp:
                # Create and activate user
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password1']
                )
                messages.success(request, "Registration successful! You can now log in.")
                
                # Clean up all session keys
                for key in ['otp', 'pending_registration', 'otp_created_at', 'registration_email']:
                    if key in request.session:
                        del request.session[key]
                        
                return redirect('login')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return render(request, 'registration/register.html', {
                    'otp_phase': True,
                    'email': email
                })
        
        # --- Phase 3: Resend OTP ---
        elif 'resend_otp' in request.POST:
            email = request.session.get('registration_email')
            
            if not email:
                messages.error(request, "Your session has expired. Please start over.")
                return redirect('register')

            # Generate and send NEW OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['otp_created_at'] = time.time() # Reset timer

            send_mail(
                subject='Your New TweetApp Verification Code',
                message=f"""Hello { email },

                    Your new one-time verification code (OTP) is:

                    { otp }

                    This code is valid for the next 5 minutes.

                    The TweetApp Team
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )

            messages.info(request, f"A new OTP has been sent to {email}. It will expire in 5 minutes.")
            return render(request, 'registration/register.html', {
                'otp_phase': True,
                'email': email
            })

    else:
        form = UserRegistrationsForm()
    return render(request, 'registration/register.html', {'form': form})



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

