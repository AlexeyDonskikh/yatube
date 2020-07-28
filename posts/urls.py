from django.urls import path

from posts import views

urlpatterns = [
    path("", views.index, name="index"),
    # Страниц группы постов
    path("group/<slug:slug>/", views.group_posts, name='group_posts'),
    # Создание нового поста
    path("new/", views.new_post, name='new_post'),
    # Страница с постами авторов,
    # на которые подписан авторизованный пользователь
    path("follow/", views.follow_index, name="follow_index"),
    # Профайл пользователя
    path('<str:username>/', views.profile, name='profile'),
    # Просмотр записи
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    # Редактирование поста
    path(
        '<str:username>/<int:post_id>/edit/',
        views.post_edit,
        name='post_edit'
    ),
    # Добавление комментария
    path("<username>/<int:post_id>/comment",
         views.add_comment, name="add_comment"),
    # Подписаться на пользователя
    path("<str:username>/follow/",
         views.profile_follow, name="profile_follow"),
    # Отписаться от пользователя
    path("<str:username>/unfollow/",
         views.profile_unfollow, name="profile_unfollow"),
]
