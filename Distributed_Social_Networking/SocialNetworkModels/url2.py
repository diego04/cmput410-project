from django.conf.urls import patterns, url

from SocialNetworkModels import views

urlpatterns = patterns('SocialNetworkModels.views',
    url(r'', 'user_login', name='user_login'), # NEW MAPPING!
)
