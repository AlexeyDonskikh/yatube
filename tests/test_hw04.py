from unittest import TestCase
from django.test import Client
from posts.models import User, Post
from django.urls import reverse


def check_text(client, user, post, text):
    """ Проверяем наличие поста на странице этого поста,
    на странице пользователя и на главной странице сайта """

    # Проверяем публикацию на персональной странице пользователя
    response = client.get("/user_test/")
    assert response.context['count'] == 1, 'На странице пользователя неправильно отображается количество постов'
    assert text in response.content.decode('utf8'), 'Не найден текст поста на странице'

    # Проверяем публикацию на странице публикации
    url = reverse('post', kwargs={'username': user.username, 'post_id': post.pk})
    response = client.get(url)
    assert response.status_code == 200, 'Страница публикации не найдена'
    assert response.context['post'].text == text, 'На странице публикации неправильный текст'

    # Проверяем публикацию на главной странице
    url = reverse('index')
    response = client.get(url)
    assert text in response.content.decode('utf8'), 'Не найден текст поста на странице'


class ProfileTest(TestCase):
    def setUp(self):
        # создание тестовых клиентов: авторизованного и неавторизованного
        self.auth_client = Client()
        self.non_auth_client = Client()
        # создаём пользователя
        self.user = User.objects.create_user(
            username="user_test", email="user_test@emeil.com", password="12345"
        )
        # создаём пост от имени пользователя
        self.post = Post.objects.create(
            text="Текст нового поста тестового пользователя",
            author=self.user)

        self.auth_client.login(username="user_test", password="12345")

    def test_profile(self):
        """После регистрации пользователя создается его персональная страница"""
        # формируем GET-запрос к странице сайта
        response = self.auth_client.get("/user_test/")

        # проверяем что страница найдена
        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, f'''Страница пользователя работает неправильно. Ошибка: `{e}`'''

    def test_new_post(self):
        """Авторизованный пользователь может опубликовать пост (new)"""

        url = reverse('new_post')
        url_index = reverse('index')

        # Проверяем, что страница `/new/` найдена
        try:
            response = self.auth_client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, f'''Страница `/new` работает неправильно. Ошибка: `{e}`'''

        # Проверяем перенаправление на главную страницу сайта
        response = self.auth_client.post(url, data={'text': self.post.text})
        try:
            self.assertIn(response.status_code, (301, 302))
        except Exception as e:
            assert False, f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        assert response.url == url_index, 'Не перенаправляет на главную страницу `/`'

    def test_check_new_post(self):
        """После публикации поста новая запись появляется на главной странице сайта (index)
        , на персональной странице пользователя (profile),
        и на отдельной странице поста (post)"""

        check_text(self.auth_client, self.user, self.post, self.post.text)

    def test_non_auth_new_post(self):
        """Неавторизованный посетитель не может опубликовать пост
        (его редиректит на страницу входа)"""

        response = self.non_auth_client.post("/new/", data={'text': self.post.text})
        assert response.status_code in (301, 302), 'Не перенаправляет на другую страницу'

    def test_edit_post(self):
        """Авторизованный пользователь может отредактировать свой пост
        и его содержимое изменится на всех связанных страницах"""

        url = reverse('post_edit', kwargs={'username': self.user.username, 'post_id': self.post.pk})

        # Проверяем, что страница редактирования поста найдена
        try:
            response = self.auth_client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, f'''Страница редактирования поста работает неправильно. Ошибка: `{e}`'''

        # Редактируем данный пост
        new_text = 'Отредактированный текст поста'
        response = self.auth_client.post(url, data={'text': new_text})
        try:
            self.assertIn(response.status_code, (301, 302))
        except Exception as e:
            assert False, f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        check_text(self.auth_client, self.user, self.post, new_text)

    def tearDown(self):
        # Clean up after each test
        self.user.delete()
        self.post.delete()
