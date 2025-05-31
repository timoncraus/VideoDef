from django.test import TestCase
from account.models import User, Role, Gender, Profile, get_random_filename, get_avatar_path
from unittest.mock import patch


class ModelTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="Родитель")
        self.gender = Gender.objects.create(name="Мужской")
        self.profile = Profile.objects.create(
            first_name="Иван",
            last_name="Иванов",
            patronymic="Иванович",
            date_birth="1990-01-01",
            role=self.role,
            gender=self.gender
        )

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "Родитель Иванов Иван Иванович")

    def test_role_display_when_none(self):
        profile = Profile.objects.create(
            first_name="Петр",
            last_name="Петров",
            patronymic="Петрович",
            date_birth="1991-02-02",
            role=None,
            gender=self.gender
        )
        self.assertEqual(profile.role_display, "Неизвестно")

    def test_user_create_and_id_generation(self):
        user = User.objects.create(
            username="testuser",
            email="test@example.com",
            phone_number="+79991234567",
            profile=self.profile
        )
        self.assertEqual(len(user.unique_id), 7)
        self.assertTrue(all(char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' for char in user.unique_id))

    def test_create_user_without_username(self):
        with self.assertRaisesMessage(ValueError, "Пользователь должен иметь логин"):
            User.objects.create_user(username=None, email="test@example.com", password="123456")

    def test_create_superuser(self):
        user = User.objects.create_superuser(username="admin", email="admin@example.com",
                                             password="adminpass")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_authenticate_by_username(self):
        user = User.objects.create_user(username="testuser2", email="test2@example.com",
                                        password="pass1234", profile=self.profile)
        authenticated_user = User.objects.authenticate_user("testuser2", "pass1234")
        self.assertEqual(authenticated_user, user)

    def test_authenticate_by_email(self):
        user = User.objects.create_user(username="emailuser", email="email@example.com",
                                        password="emailpass", profile=self.profile)
        authenticated_user = User.objects.authenticate_user("email@example.com", "emailpass")
        self.assertEqual(authenticated_user, user)

    def test_authenticate_by_phone(self):
        user = User.objects.create_user(username="phoneuser", email="phone@example.com",
                                        password="phonepass", phone_number="+71234567890", profile=self.profile)
        authenticated_user = User.objects.authenticate_user("+71234567890", "phonepass")
        self.assertEqual(authenticated_user, user)

    def test_authenticate_by_unique_id(self):
        user = User.objects.create_user(username="iduser", email="id@example.com",
                                        password="idpass", phone_number="+79991231212", profile=self.profile)
        uid = user.unique_id
        authenticated_user = User.objects.authenticate_user(uid, "idpass")
        self.assertEqual(authenticated_user, user)

    def test_authenticate_invalid_login(self):
        with self.assertRaises(ValueError):
            User.objects.authenticate_user("unknown", "any")

    def test_authenticate_invalid_password(self):
        user = User.objects.create_user(username="wrongpass", email="wrong@example.com",
                                        password="correctpass", profile=self.profile)
        with self.assertRaises(ValueError):
            User.objects.authenticate_user("wrongpass", "wrongpass")

    def test_get_random_filename(self):
        filename = get_random_filename()
        self.assertEqual(len(filename), 32)

    def test_get_avatar_path(self):
        filename = "photo.jpg"
        path = get_avatar_path(None, filename)
        self.assertTrue(path.replace("\\", "/").startswith("avatars/"))
        self.assertTrue(path.endswith(".jpg"))

    def test_get_avatar_path_with_existing_file(self):
        with patch("os.path.exists", side_effect=[True, False]):
            path = get_avatar_path(None, "test.png")
            self.assertTrue(path.replace("\\", "/").startswith("avatars/"))
            self.assertTrue(path.endswith(".png"))

    def test_generate_unique_id_conflict(self):
        user = User(username="tempuser", email="temp@example.com", phone_number="+79991234567", profile=self.profile)
        taken_id = "ABCDEFG"
        with patch("random.choices", side_effect=[[c for c in taken_id], [c for c in "HIJKLMN"]]):
            with patch("account.models.User.objects.filter") as mock_filter:
                mock_filter.side_effect = [
                    type("QuerySet", (), {"exists": lambda self: True})(),
                    type("QuerySet", (), {"exists": lambda self: False})()
                ]
                new_id = user.generate_unique_id()
                self.assertEqual(new_id, "HIJKLMN")
