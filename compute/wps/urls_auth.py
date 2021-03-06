from django.conf.urls import url

import views

# Should the auth views/models be split into their own app?

urlpatterns = [
    url(r'^create/$', views.create, name='create'),
    url(r'^update/$', views.update, name='update'),
    url(r'^user/$', views.user_details, name='user'),
    url(r'^user/stats/$', views.user_stats, name='stats'),
    url(r'^user/regenerate/$', views.regenerate),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^login/openid/$', views.user_login_openid, name='login_openid'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^login/oauth2/$', views.login_oauth2, name='oauth2'),
    url(r'^login/mpc/$', views.login_mpc, name='mpc'),
    url(r'^reset/$', views.reset_password),
    url(r'^forgot/username/$', views.forgot_username),
    url(r'^forgot/password/$', views.forgot_password),
    url(r'^callback/$', views.oauth2_callback),
    url(r'^callback/openid/$', views.user_login_openid_callback),
]
