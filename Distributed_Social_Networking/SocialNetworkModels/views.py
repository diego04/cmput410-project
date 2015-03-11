from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.shortcuts import render, redirect,render_to_response
from SocialNetworkModels.models import Posts, Author, Friends, FriendManager, Follows, FollowManager, FriendManager
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from urlparse import urlparse
from django.db import IntegrityError
from django.contrib import messages

#from django.core.serializers.json import DjangoJSONEncoder
#from django.core import serializers

import json

#user login page
def user_login(request):
    #test if user can successfully login
    error =False
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = authenticate(username=username, password=password)
            u = User.objects.get(username=username)
            if user!=None:
                if u.username == 'admin':
                    login(request, user)
                    return redirect('/home')

                elif user:
                    login(request, user)
                    return redirect('/home')
                else:
                    return render(request, 'LandingPage/login.html',{'error': 'not approved'})
            else:
                error = True
                return render(request, 'LandingPage/login.html',{'error': error})
        except:
            error = True
            return render(request, 'LandingPage/login.html',{'error': error})
    elif request.method == 'GET':
        if request.user.is_authenticated():
            return redirect('/home')
        else:
            return render(request, 'LandingPage/login.html',{'error': error})

    else:
        return render(request, 'LandingPage/login.html',{'error': error})
    
#home page, display after user login successfully
@login_required   
def home(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            user = request.user
            post = Posts.objects.all()
            ourfriend=[]
            FOAF=[]
            allfriends =Friends.friendmanager.getFriends(request.user)
            #get friend of user
            for afriend in allfriends:
                ourfriend.append(afriend.reciever.get_username())
                friendOfFriend =Friends.friendmanager.getFriends(afriend)
                for friend in friendOfFriend:
                    if friend.reciever.get_username() not in FOAF and friend.reciever.get_username() != request.user:
                        FOAF.append(friend.reciever.get_username())
                
            #friends = Friends.objects.all()
            #return HttpResponse(len(post))
            count = len(post)
        
            try:
                return render(request, 'LandingPage/home.html',{'posts':post, 'user':user, 'FOAF':FOAF,'friend':ourfriend,'lenn':count})
            except Author.DoesNotExist:
                return render(request, 'LandingPage/login.html',{'error': False})   
    elif request.method =='POST':
        return render(request, 'LandingPage/home.html')


def register(request):
    context= RequestContext(request)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        github_username= request.POST.get('github')
        picture = request.FILES.get('picture')
        
        if len(User.objects.filter(username =username))>0:
            return render(request, 'LandingPage/register.html',{'username':'username already exist'})
        else:
            if username != None and password != None:
                user=User.objects.create_user(username ,email,password)
                user.save()
                author= Author.objects.create(user=user,github_username=github_username,picture = picture )
                author.save()
                return redirect('/login')

    return render(request, 'LandingPage/register.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('/')

@login_required
def search_users(request):
    #search for users
    if request.method == 'GET':
        if request.user.is_authenticated():
            try:
                #this needs to be paginated later
                authors = Author.objects.all()
                #follows = Follows()
                followed = Follows.followManager.getFollowing(request.user)
                allfriends = Friends.friendmanager.getFriends(request.user)


                #if this got turned into a json, can do client side
                ourfollows = []
                for afollow in followed:
                    ausername = afollow.followed.get_username()
                    ourfollows.append('{s}'.format(s=ausername))

                #find the user/authors friends
                ourfriends = []
                for afriend in allfriends:
                    afriendusername = ourfriends.reciever.get_username()
                    ourfriends.append('{s}'.format(s=afriendusername))

                return render(request, 'LandingPage/search_users.html', {'authors': authors, 'followed': ourfollows, 'allfriends': ourfriends})
            except Author.DoesNotExist:
                return redirect('/login')
    else:
        return redirect('/login')


@login_required
def search_posts(request):
    #search for users
    if request.method == 'GET':
        if request.user.is_authenticated():
            try:
                #this needs to be paginated later
                posts = Posts.objects.all()
                return render(request, 'LandingPage/search_users.html',{'posts': posts})
            except Author.DoesNotExist:
                return redirect('/login')
    else:
        return redirect('/login')


@login_required
def add_friend(request, reciever_pk):
    #actually right now your adding following
    #search for users
    if request.user.is_authenticated():
        try:

            follows = Follows()
            follows.follower = User.objects.get(username = request.user)
            follows.followed = User.objects.get(pk = reciever_pk)
            follows.save()

            try:
                previousfollowed = Follows.followManager.getFollowers(request.user)
                previousfollower = User.objects.get(pk = reciever_pk).username
                #following = Follows.followManager.getFollowing(previousfollower)

                ausername = ''
                test = False
                for afollow in previousfollowed:
                    ausername = afollow.getafollower
                    busername = User.objects.get(username = ausername).username
                    #return HttpResponse(previousfollower == busername)
                    if(previousfollower == busername):
                        test = True
                        break

                if (test == True):
                    friend = Friends()
                    friend.initiator = User.objects.get(username = request.user)
                    friend.reciever = User.objects.get(pk = reciever_pk)
                    friend.save()

                return redirect('/searchusers')
            except:
                 return HttpResponse('breaked at add_friend')

            return redirect('/searchusers')

        except Author.DoesNotExist:
            return redirect('/searchusers')
    else:
        return redirect('/home')

@login_required
def author_post(request):
    if request.method =='POST':
        title = request.POST.get('post_title')
        text = request.POST.get('post_text')
        visibility = request.POST.get('visibility')
        picture = request.FILES.get('picture')        
        #post =Posts.objects.create(post_author = request.user.username, 
                                  #psot_title = title, post_text= text,visibility= visibility)
        post = Posts()
        post.post_author = Author.objects.get(user = request.user)
        post.post_title = title
        post.post_text = text
        post.visibility = visibility
        post.image = None
        if picture is not None:
            post.image=picture
        post.save()
        return redirect('/home')
    else:
        return render(request, 'LandingPage/post.html')
        
    return render(request, 'LandingPage/post.html')


@login_required
def author_post_delete(request,post_id):
    user = request.user
    post = Posts.objects.get(post_id = post_id)
    conText = ''
   
    if user.author !=post.post_author:
        context = 'you have no permissions to delete this post'
        return render(request, 'LandingPage/display.html',{'message':context,'post':post})
    else:
        post.delete()
        return redirect('/home')

@login_required
def display_post(request,post_id):
    post = Posts.objects.get(post_id = post_id)
    return render(request,'LandingPage/display.html',{'post':post})
    
@login_required
def author_post_edit(request,post_id):
    if request.method =="GET":
        user = request.user
        post = Posts.objects.get(post_id = post_id)
        conText = ''
        if user.author !=post.post_author:
            context = 'you have no permissions to edit this post'
            return render(request, 'LandingPage/display.html',{'message':context,'post':post})
        else:
            return render(request, 'LandingPage/post.html',{'edit':'1','post':post})
    elif request.method =="POST":
        post = Posts.objects.get(post_id = post_id)
        post.post_title = request.POST.get('post_title')
        post.post_text = request.POST.get('post_text')
        post.visibility = request.POST.get('visibility')
        image = request.FILES.get('picture')
        if image is not None:
            post.image=image
        post.save()
    return render(request, 'LandingPage/display.html',{'post':post})
        
        

@login_required
def profile(request,edit):
    if request.user.is_authenticated():
        if request.method =='GET':
            author = Author.objects.get(user =request.user)
            username = author.user.username
            email = author.user.email
            github_username=author.github_username
            picture = author.picture
            return render(request, 'LandingPage/profile.html',{'username':username, 'email':email,'github_username' :github_username,'picture':picture,'edit':edit})
    return render(request, 'LandingPage/profile.html')


@login_required
def profile_edit(request):
    '''
    This view is used to edit the profile for the currently logged in user
    '''
    context = RequestContext(request)
    
    if request.method == "POST":
        author = request.user.author
        username = request.POST.get('username')
        email = request.POST.get('email')
        github_username = request.POST.get('github_username')	
        picture = request.FILES.get('picture')

        if username is not None and username != '':
            request.user.username = username

        if email is not None and email != '':
            request.user.email = email

        # Update: also set the github account:
        if github_username is not None:
            author.github_username = github_username

        if picture is not None:
            author.picture = picture

        try:
            # Save the User first
            request.user.save()
            # Save the Author last
            author.save()

            # Add a success flash message
            messages.info(request, "Your profile was updated successfully.")

            # Send the user to the profile screen
            return redirect('/home')
        except IntegrityError, e:
            if "username" in e.message:
                # Add the username error
                messages.error(request, "Username is already taken.")
            elif "email" in e.message:
                # Add the email error
                messages.error(request, "An account is associated to that email.")
            else:
                # Add the generic error
                messages.error(request, e.message)
        except Exception, e:
            # Add the generic error
            messages.error(request, e.message)

    return render_to_response('main/profile.html', {}, context)

