from django.urls import path

from .views import (
    PlaylistListCreateView,
    PlaylistDetailView,
    MovieDetailView,
    MovieReactionView,
    MovieSearchView,
    RatingView,
    WatchedMovieView,
    WatchlistView,
)
from .review_views import MovieReviewListCreateView, ReviewDetailView

# O {tmdb_id} das rotas é o identificador do filme no TMDB; o filme local é
# criado/sincronizado automaticamente na primeira interação.
urlpatterns = [
    path('playlists/', PlaylistListCreateView.as_view(), name='playlist-list'),
    path('playlists/<int:pk>/', PlaylistDetailView.as_view(), name='playlist-detail'),
    path("movies/search/", MovieSearchView.as_view()),
    path("movies/<int:tmdb_id>/", MovieDetailView.as_view()),
    path("movies/<int:tmdb_id>/watch/", WatchedMovieView.as_view()),
    path("movies/<int:tmdb_id>/watchlist/", WatchlistView.as_view()),
    path("movies/<int:tmdb_id>/rating/", RatingView.as_view()),
    path("movies/<int:tmdb_id>/reaction/", MovieReactionView.as_view()),
    path("movies/<int:tmdb_id>/reviews/", MovieReviewListCreateView.as_view()),
    path("reviews/<int:pk>/", ReviewDetailView.as_view()),
]
