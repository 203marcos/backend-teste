from django.contrib import admin

from .models import (
    Movie,
    MovieReaction,
    Playlist,
    PlaylistMovie,
    Rating,
    Review,
    ReviewLike,
    WatchedMovie,
    Watchlist,
)


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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "contains_spoiler", "is_active", "created_at")
    list_filter = ("is_active", "contains_spoiler")
    search_fields = ("content", "user__username", "movie__title")
    raw_id_fields = ("user", "movie")


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "review", "created_at")
    raw_id_fields = ("user", "review")


class PlaylistMovieInline(admin.TabularInline):
    model = PlaylistMovie
    raw_id_fields = ("movie",)
    extra = 0


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_public", "updated_at")
    list_filter = ("is_public",)
    search_fields = ("name", "owner__username")
    raw_id_fields = ("owner",)
    inlines = [PlaylistMovieInline]
