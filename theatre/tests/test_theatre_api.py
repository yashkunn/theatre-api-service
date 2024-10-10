import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Play, Performance, TheatreHall, Genre, Actor, Reservation
from theatre.serializers import PlayListSerializer, PlayDetailSerializer

PLAY_URL = reverse("theatre:play-list")
PERFORMANCE_URL = reverse("theatre:performance-list")
RESERVATION_URL = reverse("theatre:reservation-list")


def sample_play(**params):
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)

    return Play.objects.create(**defaults)


def sample_performance(**params):
    play = sample_play()
    theatre_hall = TheatreHall.objects.create(name="Blue", rows=20, seats_in_row=20)

    defaults = {
        "show_time": "2022-06-02 14:00:00",
        "play": play,
        "theatre_hall": theatre_hall,
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)


def image_upload_url(play_id):
    """Return URL for recipe image upload"""
    return reverse("theatre:play-upload-image", args=[play_id])


def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


class UnauthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_for_reservation(self):
        """Test that authentication is required for viewing reservations"""
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_creating_reservation(self):
        """Test that authentication is required for creating reservations"""
        performance = sample_performance()
        payload = {
            "performance": performance.id,
            "seats": [1, 2, 3],
        }
        res = self.client.post(RESERVATION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_plays(self):
        sample_play()
        sample_play()
        res = self.client.get(PLAY_URL)

        plays = Play.objects.order_by("id")
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_plays_by_genres(self):
        genre1 = Genre.objects.create(name="Genre 1")
        genre2 = Genre.objects.create(name="Genre 2")

        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        play3 = sample_play(title="Play without genres")

        play1.genres.add(genre1)
        play2.genres.add(genre2)

        res = self.client.get(PLAY_URL, {"genres": f"{genre1.id},{genre2.id}"})

        plays = Play.objects.filter(genres__in=[genre1, genre2]).distinct()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data["count"], len(serializer.data))
        self.assertEqual(res.data["results"], serializer.data)

        self.assertNotIn(PlayListSerializer(play3).data, res.data["results"])

    def test_filter_plays_by_actors(self):
        actor1 = Actor.objects.create(first_name="Actor 1", last_name="Last 1")
        actor2 = Actor.objects.create(first_name="Actor 2", last_name="Last 2")

        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        play3 = sample_play(title="Play without actors")

        play1.actors.add(actor1)
        play2.actors.add(actor2)

        res = self.client.get(PLAY_URL, {"actors": f"{actor1.id},{actor2.id}"})

        plays = Play.objects.filter(actors__in=[actor1, actor2]).distinct()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data["count"], len(serializer.data))
        self.assertEqual(res.data["results"], serializer.data)

        self.assertNotIn(PlayListSerializer(play3).data, res.data["results"])

    def test_filter_plays_by_title(self):
        play1 = sample_play(title="Play")
        play2 = sample_play(title="Another Play")
        play3 = sample_play(title="No match")

        res = self.client.get(PLAY_URL, {"title": "play"})

        plays = Play.objects.filter(title__icontains="play")
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data["count"], len(serializer.data))
        self.assertEqual(res.data["results"], serializer.data)

        self.assertIn(PlayListSerializer(play1).data, res.data["results"])
        self.assertIn(PlayListSerializer(play2).data, res.data["results"])
        self.assertNotIn(PlayListSerializer(play3).data, res.data["results"])

    def test_retrieve_playe_detail(self):
        play = sample_play()
        play.genres.add(Genre.objects.create(name="Genre"))
        play.actors.add(Actor.objects.create(first_name="Actor", last_name="Last"))

        url = detail_url(play.id)
        res = self.client.get(url)

        serializer = PlayDetailSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AuthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_reservations(self):
        """Test listing reservations for authenticated users"""
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Play",
            "description": "Description",
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # def test_create_reservation(self):
    #     """Test creating a reservation for authenticated users"""
    #     performance = sample_performance()

    #     payload = {
    #         "tickets": [
    #             {"row": 1, "seat": 1, "performance": performance.id},
    #             {"row": 1, "seat": 2, "performance": performance.id},
    #             {"row": 1, "seat": 3, "performance": performance.id},
    #         ],
    #     }
    #
    #     res = self.client.post(RESERVATION_URL, payload)
    #
    #     if res.status_code != status.HTTP_201_CREATED:
    #         print(f"Response content: {res.content}")
    #
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    #
    #     reservation = Reservation.objects.get(id=res.data["id"])
    #     self.assertEqual(reservation.user, self.user)
    #     self.assertEqual(reservation.tickets.count(), 3)


class AdminPayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_play(self):
        payload = {
            "title": "Play",
            "description": "Description",
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(play, key))

    def test_create_play_with_genres(self):
        genre1 = Genre.objects.create(name="Action")
        genre2 = Genre.objects.create(name="Adventure")
        payload = {
            "title": "Spider Man",
            "genres": [genre1.id, genre2.id],
            "description": "With Spider-Man's identity now revealed, Peter asks Doctor Strange for help.",
        }
        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        play = Play.objects.get(id=res.data["id"])
        genres = play.genres.all()
        self.assertEqual(genres.count(), 2)
        self.assertIn(genre1, genres)
        self.assertIn(genre2, genres)

    def test_create_play_with_actors(self):
        actor1 = Actor.objects.create(first_name="Tom", last_name="Holland")
        actor2 = Actor.objects.create(first_name="Tobey", last_name="Maguire")
        payload = {
            "title": "Spider Man",
            "actors": [actor1.id, actor2.id],
            "description": "With Spider-Man's identity now revealed, Peter asks Doctor Strange for help.",
        }
        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        play = Play.objects.get(id=res.data["id"])
        actors = play.actors.all()
        self.assertEqual(actors.count(), 2)
        self.assertIn(actor1, actors)
        self.assertIn(actor2, actors)


class PlayImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.play = sample_play()
        self.performance = sample_performance(play=self.play)

    def tearDown(self):
        self.play.image.delete()

    def play(self):
        """Test uploading an image to play"""
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.play.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.play.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.play.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_play_list_should_not_work(self):
        url = PLAY_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "title": "Title",
                    "description": "Description",
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(title="Title")
        self.assertFalse(play.image)

    def test_image_url_is_shown_on_play_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.play.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_play_list(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")

        res = self.client.get(PLAY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn("results", res.data)

        results = res.data["results"]
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        self.assertIn("image", results[0].keys())

    def test_image_url_is_shown_on_performance_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(PERFORMANCE_URL)

        self.assertIn("play_image", res.data[0].keys())

    def test_put_play_not_allowed(self):
        payload = {
            "title": "New play",
            "description": "New description",
        }

        play = sample_play()
        url = detail_url(play.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_play_not_allowed(self):
        play = sample_play()
        url = detail_url(play.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
