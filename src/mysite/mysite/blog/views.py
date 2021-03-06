from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import View

from .models import Post
from .forms import PostForm
from .utils import login_user_is_writer


class PostListView(View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.filter(published_date__lte=timezone.now(), is_private=False)
        posts = posts.order_by('created_date').reverse()
        context = {'posts': posts, 'is_private': False}
        return render(request, 'blog/post_list.html', context)


class PostListPrivateView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'ログインが必要です', extra_tags='danger')
            return redirect('account_login')
        
        login_user_id = request.user.id
        posts = Post.objects.filter(published_date__lte=timezone.now(), writer__id=login_user_id)
        posts = posts.order_by('created_date').reverse()
        context = {'posts': posts, 'is_private': True}
        return render(request, 'blog/post_list.html', context)
    

class PostDetailView(View):
    def get(self, request, post_id, *args, **kwargs):
        post = Post.objects.get(id=post_id)
        
        if post.is_private and (not request.user.is_authenticated):
            raise Http404('お探しのページは見つかりません')
        if post.is_private and request.user.id != post.user.id:
            raise Http404('お探しのページは見つかりません')
            
        editable = login_user_is_writer(request.user, post.writer)
        context = {'post': post, 'editable': editable}
        return render(request, 'blog/post_detail.html', context)


class PostEditView(View):
    def get(self, request, post_id, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '編集にはログインが必要です', extra_tags='danger')
            return redirect('account_login')
        
        post = Post.objects.get(id=post_id)
        if not login_user_is_writer(request.user, post.writer):
            messages.error(request, '投稿者のみ編集が可能です', extra_tags='danger')
            return redirect('post_detail', post_id=post_id)
        
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(instance=post)
        context = {'form': form}
        return render(request, 'blog/post_edit.html', context)
    
    def post(self, request, post_id, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '編集にはログインが必要です', extra_tags='danger')
            return redirect('account_login')
        
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(request.POST, instance=post)
        if not form.is_valid():
            context = {'form': form}
            messages.error(request, '正しく入力して下さい', extra_tags='danger')
            return render(request, 'blog/post_edit.html', context) 
        
        post = form.save(commit=True)
        post.writer = request.user
        post.published_date = timezone.now()
        post.save()
        messages.error(request, '編集されました', extra_tags='info')
        return redirect('post_detail', post_id=post.id)


class PostNewView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '新規投稿にはログインが必要です', extra_tags='danger')
            return redirect('account_login')
        
        form = PostForm()
        context = {'form': form}
        return render(request, 'blog/post_edit.html', context)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '新規投稿にはログインが必要です', extra_tags='danger')
            return redirect('account_login')
        
        form = PostForm(request.POST)
        if not form.is_valid():
            context = {'form': form}
            messages.error(request, '正しく入力して下さい', extra_tags='danger')
            return render(request, 'blog/post_edit.html', context) 
        
        post = form.save(commit=False)
        post.writer = request.user
        post.published_date = timezone.now()
        post.save()
        messages.error(request, '新規投稿されました', extra_tags='info')
        return redirect('post_detail', post_id=post.id)

