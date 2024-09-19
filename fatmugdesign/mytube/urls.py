from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.video_list, name='video_list'),
    path('upload/', views.upload_video, name='upload_video'),
    path('delete_video/<int:pk>/', views.delete_video, name='delete_video'),
    path('search/', views.search_subtitles, name='search_subtitles'),
    path('list_view/',views.list_view,name='list_view'),
    path('video/<int:id>/', views.video_player, name='video_player')
   ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
