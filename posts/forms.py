from django import forms
from posts.models import Post


class PostForm(forms.ModelForm):
    """ Форма для создания нового поста """
    class Meta:
        model = Post
        fields = ['group', 'text']
        help_texts = {
            'group': 'Выберите группу для размещения вашего поста',
            'text': 'Текст вашего поста',
        }
