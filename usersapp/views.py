# from typing import Any
# from django import http
# from django.db.models.query import QuerySet
# from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
# import datetime
from django.shortcuts import HttpResponseRedirect
from .models import Post, Comment, User, EmailVerification
from django.urls import reverse
from .forms import UserLoginForm, UserRegisterForm, UserProfileForm, CommentForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.views.generic import TemplateView, DetailView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.views import LoginView


class IndexView(TemplateView):
    template_name = "usersapp/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["posts"] = Post.objects.all()
        context["title"] = "Главная страница"
        return context


class CommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = "usersapp/comments.html"
    context_object_name = "comments"

    def get_queryset(self):
        queryset = Comment.objects.filter(author=self.request.user)
        return queryset


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    template_name = "usersapp/comment_create.html"
    form_class = CommentForm
    context_object_name = "comment_create"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.author = User.objects.get(id=self.request.user.id)
        comment.post = Post.objects.get(id=self.kwargs.get("pk"))
        comment.save()

        comment = Comment.objects.get(id=comment.id)
        send_mail(
            subject="У вас новый отклик на объявление!",
            message=f"Здравствуйте, {comment.post.author}. На ваше объявление оставили отклик! Посмотреть отклик: http://127.0.0.1:8000/",
            from_email="sabi.raf@yandex.ru",
            recipient_list=[comment.post.author.email],
        )
        return HttpResponseRedirect(reverse("index"))


class CommentDetailView(DetailView):
    model = Comment
    template_name = "usersapp/comment.html"
    context_object_name = "comment"


@login_required
def confirm_comment(request, **kwargs):
    if request.user.is_authenticated:
        comment = Comment.objects.get(id=kwargs.get("pk"))
        comment.status = True
        comment.save()

        comment = Comment.objects.get(id=comment.id)
        send_mail(
            subject="Форум MMORPG: Ваш отклик принят!",
            message=f"Здравствуйте, {comment.author}, Автор объявления {comment.post.title} принял Ваш отклик! Зайдите в личный кабинет:http://127.0.0.1:8000/posts/comments",
            from_email="sabi.raf@yandex.ru",
            recipient_list=[
                comment.post.author.email,
            ],
        )
        return HttpResponseRedirect(reverse("index"))
    else:
        return HttpResponseRedirect("/posts/login")


# Post
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = "usersapp/posts.html"
    # form_class = PostCreateForm
    fields = ("title", "category", "description", "file_add")
    # success_url = reverse_lazy('usersapp:profile')

    def get_success_url(self):
        self.success_url = reverse("index")
        return super().get_success_url()

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDetailView(DetailView):
    model = Post
    template_name = "usersapp/post.html"
    context_object_name = "post"


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = "usersapp/posts.html"
    fields = ("title", "category", "description")

    def get_success_url(self):
        self.success_url = reverse("index")
        return super().get_success_url()


class PostDeleteView(DeleteView):
    model = Post
    template_name = "usersapp/post_delete.html"
    context_object_name = "post_delete"

    def get_success_url(self):
        self.success_url = reverse("index")
        return super().get_success_url()


# User
class UserLoginView(LoginView):
    template_name = "usersapp/login.html"
    form_class = UserLoginForm


class UserRegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "usersapp/register.html"
    success_url = reverse_lazy("usersapp:login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Регистрация"
        return context


class UserProfileView(UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "usersapp/profile.html"

    def get_success_url(self):
        return reverse_lazy("usersapp:profile", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Личный кабинет"
        context["posts"] = Post.objects.filter(author=self.object)
        context["my_comments"] = Comment.objects.filter(author=self.object)
        return context


class EmailVereficationView(TemplateView):
    template_name = "usersapp/email_verefication.html"

    def get(self, request, *args, **kwargs):
        code = kwargs["code"]
        user = User.objects.get(email=kwargs["email"])
        email_verif = EmailVerification.objects.filter(user=user, code=code)
        if email_verif.exists() and not email_verif.first().is_expired():
            user.is_verified_email = True
            user.save()
            return super(EmailVereficationView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse("index"))
