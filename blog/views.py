from django.shortcuts import render, get_object_or_404
from blog.models import Post, Comment
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger
from django.views.generic import ListView
from django.conf import settings
from .forms import EmailPostForm , CommentForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count


# def post_list(request):
#     posts = Post.published.all()
#     return render(request,'blog/post/list.html',{'posts':posts})

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    print(tag_slug)
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        print(tag)
        object_list = object_list.filter(tags__in=[tag])
        print(object_list)
    paginator = Paginator(object_list, 3) # 3 posts in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
    # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    
    return render(request,'blog/post/list.html',{'page': page,'posts': posts, 'tag':tag})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status = 'draft',publish__year=year,publish__month=month,publish__day=day)
    comments = post.comments.filter(active=True)
    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()
        
    post_tags_ids = post.tags.values_list('id', flat=True) 
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    return render(request,'blog/post/detail.html',{'post': post,'comments': comments,'comment_form': comment_form, 'similar_posts': similar_posts})

def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='draft')
    sent = False
    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            #url_p = str(post.publish.year)+'/'+str(post.publish.month)+'/'+str(post.publish.day)+'/'+post.slug
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, settings.EMAIL_HOST_USER,[cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,'form': form,'sent': sent})

   


