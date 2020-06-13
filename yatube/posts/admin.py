from django.contrib import admin

from .models import Post


class PostAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("text", "pub_date", "author")
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ("text",)
    # добавляем возможность фильтрации по дате
    list_filter = ("pub_date",)


# при регистрации модели Post источником конфигурации для неё
# назначаем класс PostAdmin
admin.site.register(Post, PostAdmin)
