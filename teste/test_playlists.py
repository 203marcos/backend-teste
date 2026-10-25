"""
Testes dos endpoints de playlists:

    GET/POST         /api/playlists/
    GET/PATCH/DELETE /api/playlists/{id}/
    POST             /api/playlists/{id}/movies/
    DELETE           /api/playlists/{id}/movies/{tmdb_id}/

O TMDB é sempre mockado: nenhuma chamada de rede real é feita.

Executar com:
    DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test teste
"""
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.movies import tmdb
from apps.movies.models import Playlist, PlaylistMovie

from .helpers import criar_usuario, fake_get_movie

PLAYLISTS_URL = "/api/playlists/"


def playlist_url(playlist_id, suffix=""):
    return f"{PLAYLISTS_URL}{playlist_id}/{suffix}"


class PlaylistBaseTests(APITestCase):
    def setUp(self):
        self.dono = criar_usuario("dono")
        self.outro = criar_usuario("outro")
        self.client.force_authenticate(self.dono)

    def _criar_playlist(self, **data):
        payload = {"name": "Favoritos", "description": "Os melhores", "is_public": True, **data}
        response = self.client.post(PLAYLISTS_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data["id"]


class PlaylistCrudTests(PlaylistBaseTests):
    def test_criar_playlist(self):
        playlist_id = self._criar_playlist(is_public=False)

        playlist = Playlist.objects.get(pk=playlist_id)
        self.assertEqual(playlist.owner, self.dono)
        self.assertFalse(playlist.is_public)

    def test_criar_sem_nome_retorna_400(self):
        response = self.client.post(PLAYLISTS_URL, {"name": "  "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_requer_autenticacao(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(PLAYLISTS_URL).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.post(PLAYLISTS_URL, {"name": "x"}, format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_listagem_mostra_apenas_playlists_do_usuario(self):
        self._criar_playlist(name="Pública")
        self._criar_playlist(name="Privada", is_public=False)
        self.client.force_authenticate(self.outro)
        self._criar_playlist(name="Do outro")

        self.client.force_authenticate(self.dono)
        response = self.client.get(PLAYLISTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({p["name"] for p in response.data["results"]}, {"Pública", "Privada"})

    def test_playlist_publica_e_visivel_para_todos(self):
        playlist_id = self._criar_playlist()
        self.client.force_authenticate(None)

        response = self.client.get(playlist_url(playlist_id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["owner_username"], "dono")
        self.assertEqual(response.data["movies"], [])
        self.assertEqual(response.data["movies_count"], 0)

    def test_playlist_privada_so_e_visivel_para_o_dono(self):
        playlist_id = self._criar_playlist(is_public=False)

        self.assertEqual(self.client.get(playlist_url(playlist_id)).status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.outro)
        self.assertEqual(self.client.get(playlist_url(playlist_id)).status_code, status.HTTP_404_NOT_FOUND)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(playlist_url(playlist_id)).status_code, status.HTTP_404_NOT_FOUND)

    def test_dono_edita_playlist(self):
        playlist_id = self._criar_playlist()

        response = self.client.patch(
            playlist_url(playlist_id), {"name": "Renomeada", "is_public": False}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        playlist = Playlist.objects.get(pk=playlist_id)
        self.assertEqual(playlist.name, "Renomeada")
        self.assertFalse(playlist.is_public)

    def test_outro_usuario_nao_edita_nem_exclui(self):
        playlist_id = self._criar_playlist()
        self.client.force_authenticate(self.outro)

        patched = self.client.patch(playlist_url(playlist_id), {"name": "Minha"}, format="json")
        deleted = self.client.delete(playlist_url(playlist_id))

        self.assertEqual(patched.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Playlist.objects.get(pk=playlist_id).name, "Favoritos")

    def test_dono_exclui_playlist(self):
        playlist_id = self._criar_playlist()

        response = self.client.delete(playlist_url(playlist_id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Playlist.objects.exists())


@patch("apps.movies.tmdb.get_movie", side_effect=fake_get_movie)
class PlaylistMoviesTests(PlaylistBaseTests):
    def setUp(self):
        super().setUp()
        self.playlist_id = self._criar_playlist()

    def _adicionar(self, tmdb_id, playlist_id=None):
        return self.client.post(
            playlist_url(playlist_id or self.playlist_id, "movies/"), {"tmdb_id": tmdb_id}, format="json"
        )

    def test_adicionar_filmes_em_ordem(self, _):
        first = self._adicionar(550)
        second = self._adicionar(603)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        self.assertEqual(first.data["position"], 0)
        self.assertEqual(second.data["position"], 1)

        detail = self.client.get(playlist_url(self.playlist_id)).data
        self.assertEqual([item["movie"]["tmdb_id"] for item in detail["movies"]], [550, 603])
        self.assertEqual(detail["movies_count"], 2)

    def test_nao_adiciona_filme_repetido(self, _):
        self._adicionar(550)
        response = self._adicionar(550)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PlaylistMovie.objects.count(), 1)

    def test_nao_adiciona_filme_inexistente(self, mock_get_movie):
        mock_get_movie.side_effect = tmdb.TMDBNotFound("não existe")
        response = self._adicionar(999999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(PlaylistMovie.objects.exists())

    def test_tmdb_id_invalido_retorna_400(self, _):
        response = self._adicionar("abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outro_usuario_nao_adiciona_nem_remove(self, _):
        self._adicionar(550)
        self.client.force_authenticate(self.outro)

        added = self._adicionar(603)
        removed = self.client.delete(playlist_url(self.playlist_id, "movies/550/"))

        self.assertEqual(added.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(removed.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PlaylistMovie.objects.count(), 1)

    def test_playlist_privada_de_outro_retorna_404(self, _):
        self.client.force_authenticate(self.outro)
        privada_id = self._criar_playlist(is_public=False)
        self.client.force_authenticate(self.dono)

        response = self._adicionar(550, playlist_id=privada_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remover_filme(self, _):
        self._adicionar(550)

        response = self.client.delete(playlist_url(self.playlist_id, "movies/550/"))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PlaylistMovie.objects.exists())

    def test_remover_filme_ausente_retorna_404(self, _):
        self._adicionar(550)
        self.client.post("/api/movies/603/watch/")  # garante o filme 603 no catálogo local

        response = self.client.delete(playlist_url(self.playlist_id, "movies/603/"))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
