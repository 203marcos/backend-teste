from django.shortcuts import render

# Create your views here.
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Playlist
from .permissions import IsOwnerOrReadOnly
from .serializers import PlaylistSerializer


class PlaylistListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        return (
            Playlist.objects
            .filter(owner=self.request.user)
            .select_related('owner')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        queryset = Playlist.objects.select_related('owner')
        if user.is_authenticated:
            return queryset.filter(Q(is_public=True) | Q(owner=user))
        return queryset.filter(is_public=True)