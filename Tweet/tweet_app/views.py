from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from .models import Tweet
from .forms import TweetForm, UserRegistrationsForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import random
from django.core.mail import send_mail

# Create your views here.

#All the tweets
def tweet_list(request):
    tweets = Tweet.objects.all().order_by("-created_at")
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
def tweet_delete(request,tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id, user=request.user)
    if request.method == "POST":
        tweet.delete()
        return redirect("tweet_list")
    return render(request, "tweet_confirm_delete.html",{'tweet':tweet})

@login_required
def tweet_search(request):
    query = request.GET.get('search', '')
    if query:
        tweets = Tweet.objects.filter(text__icontains=query)
        if not tweets.exists():
            all_tweets = Tweet.objects.all()
            return render(request, 'tweet_list.html', {
                'tweets': all_tweets,
                'message': "No tweets found matching your search."
            })
    else:
        tweets = Tweet.objects.all()

    return render(request, 'tweet_list.html', {'tweets': tweets})

def register(request):
    if request.method == 'POST':
        # Phase 1: User submits basic info
        if 'send_otp' in request.POST:
            form = UserRegistrationsForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']

                # Generate and send OTP
                otp = str(random.randint(100000, 999999))
                request.session['pending_registration'] = form.cleaned_data
                request.session['otp'] = otp

                send_mail(
                    subject='Verify your email address for TweetApp',
                    message=f"""Hello { email },
                        Thank you for signing up with TweetApp — we’re excited to have you join our community!
                        To complete your registration and activate your account, please verify your email address.

                        Your one-time verification code (OTP) is:

                        { otp }

                        This code is valid for the next 10 minutes and can be used only once.
                        If you didn’t request this code, please ignore this email — your account will remain inactive until the code is verified.

                        After entering the OTP in the registration form, your account will be activated automatically and you’ll be able to log in to TweetApp to create and share posts, connect with others, and explore trending content.

                        For your security, please do not share this code with anyone. TweetApp will never ask for your OTP or password in any email, phone call, or message.

                        Welcome aboard,
                        The TweetApp Team
                        support@tweetapp.com
                    """,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                )

                messages.info(request, f"An OTP has been sent to {email}. Please verify it below.")
                return render(request, 'registration/register.html', {
                    'otp_phase': True,
                    'email': email
                })
        
        # Phase 2: User enters OTP to confirm
        elif 'verify_otp' in request.POST:
            entered_otp = request.POST.get('otp')
            saved_otp = request.session.get('otp')
            data = request.session.get('pending_registration')

            if entered_otp == saved_otp:
                # Create and activate user
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password1']
                )
                messages.success(request, "Registration successful! You can now log in.")
                del request.session['otp']
                del request.session['pending_registration']
                return redirect('login')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return render(request, 'registration/register.html', {'otp_phase': True})

    else:
        form = UserRegistrationsForm()
    return render(request, 'registration/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'registration/login.html')

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            login(request, user)
            return redirect('tweet_list')
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'registration/login.html')

