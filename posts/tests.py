import tempfile

from django.core.cache import cache
from django.core.cache.backends import locmem
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class ProfileTest(TestCase):
    """ Тесты постов """
    def setUp(self):
        self.auth_client = Client()
        self.non_auth_client = Client()

        self.user = User.objects.create_user(
            username="test_user", email="test_user@emeil.com", password="12345"
        )

        self.group = Group.objects.create(
            title='test_group',
            slug='test_group'
        )

        self.post = Post.objects.create(
            text="Текст нового поста тестового пользователя",
            author=self.user,
            group=self.group
        )

        self.auth_client.login(username="test_user", password="12345")

    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
    })
    def check_text(self, text):
        """ Проверяем наличие поста на странице этого поста,
        на странице пользователя, на странице группы
        и на главной странице сайта """

        url = reverse('profile', kwargs={'username': self.user.username})
        response = self.auth_client.get(url)
        self.assertContains(response, text), \
            'Не найден текст поста на странице пользователя'

        url = reverse('post',
                      kwargs={'username': self.user.username,
                              'post_id': self.post.pk}
                      )
        response = self.auth_client.get(url)
        assert response.status_code == 200, \
            'Страница публикации не найдена'
        self.assertContains(response, text), \
            'Не найден текст поста на странице публикации'

        url = reverse('group_posts', kwargs={'slug': self.group.slug})
        response = self.auth_client.get(url)
        assert response.status_code == 200, 'Страница группы не найдена'
        self.assertContains(response, text), \
            'Не найден текст поста на странице группы'

        url = reverse('index')
        response = self.auth_client.get(url)
        self.assertContains(response, text), \
            'Не найден текст поста на странице'

    def test_profile(self):
        """После регистрации пользователя создается
        его персональная страница"""
        url = reverse('profile', kwargs={'username': self.user.username})
        response = self.auth_client.get(url)

        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, \
                f'''Страница пользователя работает неправильно. 
                Ошибка: `{e}`'''

    def test_new_post(self):
        """Авторизованный пользователь может опубликовать пост (new)"""

        url = reverse('new_post')
        url_index = reverse('index')

        try:
            response = self.auth_client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, \
                f'''Страница `/new` работает неправильно. Ошибка: `{e}`'''

        response = self.auth_client.post(url, data={'text': self.post.text})
        try:
            self.assertIn(response.status_code, (301, 302))
        except Exception as e:
            assert False, \
                f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        assert response.url == url_index, \
            'Не перенаправляет на главную страницу `/`'

    def test_check_new_post(self):
        """После публикации поста новая запись появляется
        на главной странице сайта (index),
        на персональной странице пользователя (profile)
        и на отдельной странице поста (post)"""
        self.check_text(self.post.text)

    def test_non_auth_new_post(self):
        """Неавторизованный посетитель не может опубликовать пост
        (его редиректит на страницу входа)"""

        url = reverse('new_post')
        response = self.non_auth_client.post(url,
                                             data={'text': self.post.text})
        assert response.status_code in (301, 302), \
            'Не перенаправляет на другую страницу'

    def test_edit_post(self):
        """Авторизованный пользователь может отредактировать свой пост
        и его содержимое изменится на всех связанных страницах"""

        url = reverse('post_edit', kwargs={'username': self.user.username,
                                           'post_id': self.post.pk})

        try:
            response = self.auth_client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, \
                f'''Страница редактирования поста работает неправильно. 
                Ошибка: `{e}`'''

        new_text = 'Отредактированный текст поста'
        response = self.auth_client.post(url, data={'group': self.group.id,
                                                    'text': new_text})
        try:
            self.assertIn(response.status_code, (301, 302))
        except Exception as e:
            assert False, \
                f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        self.check_text(new_text)

    def test_404(self):
        """Проверка,возвращает ли сервер код 404,
        если страница не найдена."""
        response = self.non_auth_client.get("/test_404_url/")
        assert response.status_code == 404, \
            'Страница 404 для неавторизованного пользователя ' \
            'работает неправильно'

        response = self.non_auth_client.get("/test_404_url/")
        assert response.status_code == 404, \
            'Страница 404 для авторизованного пользователя ' \
            'работает неправильно'

    def test_image(self):
        """Проверка главной страницы, страницы пользователя,
         страницы поста и страницы группы на наличие картинки"""

        url = reverse('new_post')

        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                with open('media/test/test_img.jpg', 'rb') as img:
                    self.auth_client.post(
                        url,
                        {'author': self.user,
                         'text': 'Попытка создать пост '
                                 'с неграфическим файлом',
                         'image': img,
                         "group": self.group.id},
                        follow=True
                    )

                    post = Post.objects.last()
                    pages = [reverse('index'),
                             reverse('profile',
                                     kwargs={'username': self.user.username}),
                             reverse('post',
                                     kwargs={'username': self.user.username,
                                             'post_id': post.id}),
                             reverse('group_posts',
                                     kwargs={'slug': self.group.slug})]

                    try:
                        self.assertTrue(post.image)
                    except Exception as e:
                        assert False, f'''Картинка не найдена. Ошибка: `{e}`'''

                    for page in pages:
                        response = self.auth_client.get(page)
                        try:
                            self.assertContains(response, "<img",
                                                status_code=200)
                        except Exception as e:
                            assert False, \
                                f'''Тег <img> на странице {page} не найден.
                                Ошибка: `{e}`'''

    def test_load_not_image(self):
        """Проверка, что срабатывает защита от загрузки файлов
        неграфических форматов"""
        url = reverse('new_post')
        with tempfile.TemporaryDirectory() as temp_directory:
            with override_settings(MEDIA_ROOT=temp_directory):
                with open('media/test/test.txt', 'rb') as img:
                    response = self.auth_client.post(
                        url,
                        {'author': self.user,
                         'text': 'Попытка создать пост '
                                 'с неграфическим файлом',
                         'image': img,
                         "group": self.group.id},
                        follow=True
                    )
            try:
                self.assertFormError(response, 'form', 'image',
                                     'Загрузите правильное изображение. '
                                     'Файл, который вы загрузили, '
                                     'поврежден или не является изображением.')
            except Exception as e:
                assert False, \
                    f'''Защита от загрузки неграфического файла не работает. 
                    Ошибка: `{e}`'''

    # def tearDown(self):
    #     """ Удаляем данные после теста """
    #     self.user.delete()
    #     self.group.delete()
    #     self.post.delete()


class TestCache(TestCase):
    """ Тесты кеша """
    def setUp(self):
        self.auth_client = Client()

        self.user = User.objects.create_user(
            username="test_user", email="test_user@emeil.com", password="12345"
        )

        self.group = Group.objects.create(
            title='test_group',
            slug='test_group'
        )

        self.post = Post.objects.create(
            text="Проверка кеша",
            author=self.user,
            group=self.group
        )

        self.auth_client.login(username="test_user", password="12345")

    def test_cache_index(self):
        """ Тест кеша главной страницы """
        cache.clear()

        url = reverse('new_post')
        response = self.auth_client.post(url, data={'text': self.post.text})

        try:
            self.assertRedirects(response, '/')
        except Exception as e:
            assert False, \
                f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        # проверка, что OrderedDict() содержит кеш
        try:
            self.assertTrue(locmem._caches[''])
        except Exception as e:
            assert False, \
                f'''Кеш не создан после создания поста. Ошибка: `{e}`'''

        # Попробуем найти в кеше текст нашего поста
        # Текст страницы из кеша в bytes
        page = locmem._caches[''].popitem()[1]
        # Текст нашего поста в bytes
        post_text = self.post.text.encode()
        # Ищем текст
        try:
            page.index(post_text)
        except Exception as e:
            assert False, \
                f'''Текст поста на странице в кеше не найден. Ошибка: `{e}`'''

        cache.clear()
        try:
            self.assertFalse(locmem._caches[''])
        except Exception as e:
            assert False, f'''Кеш не очищен. Ошибка: `{e}`'''


class TestFollow(TestCase):
    """ Тесты подписок """
    def setUp(self):
        # автор постов
        self.author_client = Client()
        # авторизованный клиент, подписанный на автора постов
        self.auth_client_1 = Client()
        # авторизованный клиент, неподписанный на автора постов
        self.auth_client_2 = Client()

        self.author = User.objects.create_user(
            username="author", email="author@emeil.com", password="12345"
        )
        self.user_1 = User.objects.create_user(
            username="test_user_1", email="test_user_1@emeil.com",
            password="user12345"
        )
        self.user_2 = User.objects.create_user(
            username="test_user_2", email="test_user_2@emeil.com",
            password="user54321"
        )

        self.group = Group.objects.create(
            title='test_group',
            slug='test_group'
        )

        self.post = Post.objects.create(
            text="Проверка подписок",
            author=self.author,
            group=self.group
        )

        self.author_client.login(username="author", password="12345")
        self.auth_client_1.login(username="test_user_1", password="user12345")
        self.auth_client_2.login(username="test_user_2", password="user54321")

    def check_follow_unfollow(self, url, following):
        response = self.auth_client_1.post(url, follow=True)

        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            if following:
                assert False, \
                    f'''Страница подписки работает неправильно. 
                    Ошибка: `{e}`'''
            else:
                assert False, \
                    f'''Страница отписки работает неправильно. 
                    Ошибка: `{e}`'''

        try:
            if following:
                self.assertTrue(
                    Follow.objects.filter(user=self.user_1,
                                          author=self.author).exists()
                )
            else:
                self.assertFalse(
                    Follow.objects.filter(user=self.user_1,
                                          author=self.author).exists()
                )
        except Exception as e:
            if following:
                assert False, \
                    f'''Пользователь user_1 не смог подписатсья на пользователя
                    author. Ошибка: `{e}`'''
            else:
                assert False, \
                    f'''Пользователь user_1 не смог отписаться от 
                    пользователя author. Ошибка: `{e}`'''

    def test_follow(self):
        """ Пользователь user_1 подписывается на пользователя author"""
        url = reverse('profile_follow',
                      kwargs={'username': self.author.username})
        self.check_follow_unfollow(url, following=True)

    def test_unfollow(self):
        """ Пользователь user_1 отписывается от пользователя author"""
        url = reverse('profile_unfollow',
                      kwargs={'username': self.author.username})
        self.check_follow_unfollow(url, following=False)

    def test_follow_post(self):
        """ Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него """
        url = reverse('profile_follow',
                      kwargs={'username': self.author.username})
        self.auth_client_1.post(url, follow=True)

        url = reverse('follow_index')
        response = self.auth_client_1.get(url)

        try:
            self.assertContains(response, self.post.text, status_code=200)
        except Exception as e:
            assert False, \
                f'''Текст автора не найден в ленте пользователя, 
                подписанного на него. Ошибка: `{e}`'''

        response = self.auth_client_2.get(url)
        try:
            self.assertNotContains(response, self.post.text, status_code=200)
        except Exception as e:
            assert False, \
                f'''Текст автора найден в ленте пользователя, 
                не подписанного на него. Ошибка: `{e}`'''


class TestComments(TestCase):
    """ Тесты комментариев """
    def setUp(self):
        # автор постов
        self.author_client = Client()
        # авторизованный пользователь
        self.auth_client = Client()
        # неавторизованный пользователь
        self.non_auth_client = Client()

        self.author = User.objects.create_user(
            username="author", email="author@emeil.com", password="12345"
        )
        self.auth_user = User.objects.create_user(
            username="auth_user", email="auth_user@emeil.com", password="54321"
        )

        self.group = Group.objects.create(
            title='test_group',
            slug='test_group'
        )

        self.post = Post.objects.create(
            text="Проверка комментариев",
            author=self.author,
            group=self.group
        )

        self.author_client.login(username="author", password="12345")
        self.auth_client.login(username="auth_user", password="54321")

    def test_comments(self):
        """ Только авторизированный пользователь может комментировать посты """
        url = reverse(
            'add_comment',
            kwargs={'username': self.author.username, 'post_id': self.post.id}
        )
        comment_text_auth = 'Текст тестового комментария авторизованного ' \
                            'пользователя'
        comment_text_non_auth = 'Текст тестового комментария' \
                                ' неавторизованного пользователя'

        response = self.auth_client.post(
            url, data={'text': comment_text_auth}, follow=True
        )
        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, \
                f'''Страница добавления комментария работает неправильно. 
                Ошибка: `{e}`'''

        url = reverse('post', kwargs={'username': self.author.username,
                                      'post_id': self.post.id})
        response = self.auth_client.get(url)
        try:
            self.assertContains(response, comment_text_auth, status_code=200)
        except Exception as e:
            assert False, f'''Комментарий не найден. Ошибка: `{e}`'''

        response = self.non_auth_client.post(
            url, data={'text': comment_text_non_auth}, follow=True
        )

        try:
            self.assertNotContains(response, comment_text_non_auth,
                                   status_code=200)
        except Exception as e:
            assert False, f'''Комментарий найден. Ошибка: `{e}`'''
