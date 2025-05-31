from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from account import views
from account.models import Role, Gender, Profile

User = get_user_model()


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.role = Role.objects.create(name="Родитель")
        self.gender = Gender.objects.create(name="Мужской")

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            phone_number='+1234567890',
        )
        self.user.profile = Profile.objects.create(
            first_name='Имя',
            last_name='Фамилия',
            patronymic='Отчество',
            date_birth='2000-01-01',
            role=self.role,
            gender=self.gender,
        )
        self.user.save()

    def test_home_view(self):
        response = self.client.get(reverse('account:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/home.html')

    def test_about_view(self):
        response = self.client.get(reverse('account:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/about.html')

    def test_account_view_not_authenticated(self):
        response = self.client.get(reverse('account:account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/account.html')

    def test_account_view_authenticated_get(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('account:account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/edit_form.html')

    def test_account_view_authenticated_post_invalid(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('account:account'), data={
            'username': '',
            'email': 'invalidemail',
            'phone_number': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пожалуйста, исправьте ошибки")

    def test_register_view_get(self):
        response = self.client.get(reverse('account:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register_form.html')

    def test_register_view_post_valid(self):
        response = self.client.post(reverse('account:register'), {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'phone_number': '+79999999999',
                'password1': 'StrongPassword123',
                'password2': 'StrongPassword123',
                'first_name': 'Новый',
                'last_name': 'Пользователь',
                'patronymic': 'Тестович',
                'date_birth': '01.01.2000',
                'role': self.role.id,
                'gender': self.gender.id
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вы успешно зарегистрировались!")

    def test_login_view_get(self):
        response = self.client.get(reverse('account:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login_form.html')

    def test_login_view_post_valid(self):
        response = self.client.post(reverse('account:login'), {
            'identifier': 'testuser',
            'password': 'password123'
        }, follow=True)
        self.assertContains(response, "Вы вошли в систему")

    def test_login_view_post_invalid(self):
        response = self.client.post(reverse('account:login'), {
            'identifier': 'wronguser',
            'password': 'wrongpass'
        })
        self.assertContains(response, "Неверный логин")

    def test_logout_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('account:logout'), follow=True)
        self.assertContains(response, "Вы вышли из системы!")

    def test_view_other_user(self):
        response = self.client.get(reverse('account:view_other_user', args=[self.user.unique_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/user_view.html')
        self.assertContains(response, self.user.username)
