from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by("-pub_date")[:12]
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  "group.html",
                  {"group": group,
                   "posts": posts,
                   'page': page,
                   'paginator': paginator}
                  )


@login_required
def new_post(request):
    """ Добавить новую запись """
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')

    return render(request,
                  'new_post.html',
                  {'form': form, 'edit': False, 'username': request.user}
                  )


def profile(request, username):
    """ Отобразить все посты пользователя """
    author = get_object_or_404(User, username=username)
    posts = author.posts.order_by("-pub_date").all()
    count = posts.count()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    follow_status = None
    if request.user.username:
        follow_status = Follow.objects.filter(user=request.user,
                                              author=author).exists()

    followers = Follow.objects.filter(author=author).count
    following_authors = Follow.objects.filter(user=author).count

    return render(
        request,
        'profile.html',
        {'author': author,
         'full_name': author.get_full_name,
         'count': count,
         'page': page,
         'paginator': paginator,
         "following": follow_status,
         'followers': followers,
         'following_authors': following_authors}
    )


def post_view(request, username, post_id):
    """ Отобразить конкретный пост пользователя """
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.order_by('-created')
    form = CommentForm()

    followers = Follow.objects.filter(author=author).count
    following_authors = Follow.objects.filter(user=author).count

    return render(
        request,
        'post.html',
        {'author': author,
         'full_name': author.get_full_name,
         'count': count,
         'comments': comments,
         'post': post,
         'form': form,
         'followers': followers,
         'following_authors': following_authors}
    )


@login_required
def post_edit(request, username, post_id):
    """ Редактирование поста пользователя """
    post = get_object_or_404(Post, pk=post_id)
    url = reverse('post',
                  kwargs={'username': username,
                          'post_id': post_id}
                  )

    if post.author != request.user:
        return redirect(url)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect(url)

    return render(request,
                  'new_post.html',
                  {'form': form,
                   'edit': True,
                   'username': username,
                   'post_id': post_id,
                   'post': post}
                  )


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    """ Добавление комментария к посту """
    post = get_object_or_404(Post, pk=post_id)
    url = reverse('post', kwargs={'username': username,
                                  'post_id': post_id})

    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(url)

    return redirect(url)


@login_required
def follow_index(request):
    """ Отображение страницы с постами подписок """
    posts_list = Post.objects.filter(
        author__following__user=request.user).select_related(
        'author', 'group').order_by("-pub_date")
    paginator = Paginator(posts_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  "follow.html",
                  {'paginator': paginator,
                   'page': page}
                  )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if request.user != author:
        Follow.objects.get_or_create(user=request.user,
                                     author=author)

    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)

    if request.user == author:
        return redirect("profile", username=username)

    Follow.objects.filter(user=request.user,
                          author=author).delete()
    return redirect("profile", username=username)
