from django.urls import path
from .views import PlaylistListCreateView, PlaylistDetailView

urlpatterns = [
    path('playlists/', PlaylistListCreateView.as_view(), name='playlist-list'),
    path('playlists/<int:pk>/', PlaylistDetailView.as_view(), name='playlist-detail'),
]