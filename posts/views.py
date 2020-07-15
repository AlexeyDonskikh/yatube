from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from posts.models import Post, Group, User
from posts.forms import PostForm


def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)  # показывать по 10 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by("-pub_date")[:12]
    paginator = Paginator(posts, 10)  # показывать по 10 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "posts": posts, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    """ Добавить новую запись """
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request,
                      'new_post.html',
                      {'form': form, 'edit': False, 'username': request.user}
                      )
    form = PostForm()
    return render(request,
                  'new_post.html',
                  {'form': form, 'edit': False, 'username': request.user}
                  )


def profile(request, username):
    """ Отобразить все посты пользователя """
    author = get_object_or_404(User, username=username)
    posts = author.posts.order_by("-pub_date").all()
    count = posts.count()
    paginator = Paginator(posts, 10)  # показывать по 10 записей на странице.
    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {'author': author,
         'full_name': author.get_full_name,
         'count': count,
         'page': page,
         'paginator': paginator}
    )


def post_view(request, username, post_id):
    """ Отобразить конкретный пост пользователя """
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()
    post = get_object_or_404(Post, pk=post_id)
    return render(
        request,
        'post.html',
        {'author': author,
         'full_name': author.get_full_name,
         'count': count,
         'post': post}
    )


@login_required
def post_edit(request, username, post_id):
    """ Редактирование поста пользователя """
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(reverse('post', kwargs={'username': username, 'post_id': post_id}))

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(reverse('post', kwargs={'username': username, 'post_id': post_id}))
        return render(request,
                      'new_post.html',
                      {'form': form, 'edit': True, 'username': username, 'post_id': post_id, 'post': post}
                      )

    form = PostForm(instance=post)
    return render(request,
                  'new_post.html',
                  {'form': form, 'edit': True, 'username': username, 'post_id': post_id, 'post': post}
                  )
