from django.urls import path

from .views import PlaylistListCreateView, PlaylistDetailView, MovieDetailView, MovieSearchView

# O {tmdb_id} das rotas é o identificador do filme no TMDB; o filme local é
# criado/sincronizado automaticamente na primeira interação.
urlpatterns = [
    path('playlists/', PlaylistListCreateView.as_view(), name='playlist-list'),
    path('playlists/<int:pk>/', PlaylistDetailView.as_view(), name='playlist-detail'),
    path("movies/search/", MovieSearchView.as_view()),
    path("movies/<int:tmdb_id>/", MovieDetailView.as_view()),
]
