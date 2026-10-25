from django.contrib import admin

from .models import Movie, MovieReaction, Rating, WatchedMovie, Watchlist


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "provider", "provider_movie_id", "release_date")
    search_fields = ("title", "original_title", "provider_movie_id")
    list_filter = ("provider",)


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "watched_at")
    raw_id_fields = ("user", "movie")


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "added_at")
    raw_id_fields = ("user", "movie")


@admin.register(MovieReaction)
class MovieReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "reaction", "updated_at")
    list_filter = ("reaction",)
    raw_id_fields = ("user", "movie")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "stars", "updated_at")
    list_filter = ("stars",)
    raw_id_fields = ("user", "movie")
