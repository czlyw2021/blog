#引入redirect重定向模块
from django.core import paginator
from django.shortcuts import render,redirect
from django.utils import html
import markdown
#引入HttpResponse
from django.http import HttpResponse, request
#引入定义的ArticlePostForm
from .forms import ArticlePostForm
#引入user模型
from django.contrib.auth.models import User
#导入数据模型ArticlePost
from .models import ArticlePost,ArticleColumn
from django.contrib.auth.decorators import login_required,permission_required
from django.core.paginator import Page, Paginator
from django.db.models import Q
from comment.models import Comment
from .models import ArticleColumn
#引入评论表单
from comment.forms import CommentForm
#   def article_list(request):
    #取出所有博客文章
    # articles = ArticlePost.objects.all()
    # 修改变量名称（articles -> article_list）
    #article_list = ArticlePost.objects.all()
    #每页显示1篇文章
    #paginator =Paginator(article_list,1)
    #获取url中的页码
    #page = request.GET.get('page')
    #将导航对象对于的页码内用返回给articles
    #articles = paginator.get_page(page)
    #需要传递给模板（templates）的对象
    #context = { 'articles': articles }
    #render函数：载入模板，并返回context对象
    #return render(request, 'article/list.html', context)
    
    
#重写article_list视图实现按照浏览量等来排序
def article_list(request):
    #从url中提取查询参数
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')
     # 初始化查询集
    article_list = ArticlePost.objects.all()

    # 搜索查询集
    if search:
        article_list = article_list.filter(
            Q(title__icontains=search) |
            Q(body__icontains=search)
        )
    else:
        search = ''

    # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)

    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')

    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    # 需要传递给模板（templates）的对象
    context = {
        'articles': articles,
        'order': order,
        'search': search,
        'column': column,
        'tag': tag,
    }

    return render(request, 'article/list.html', context)
#文章详情
def article_detail(request, id):
    #取出相应的文章
    article = ArticlePost.objects.get(id=id)
    # 取出文章评论
    comments = Comment.objects.filter(article=id)
    if request.user != article.author:
        #浏览量+1
        article.total_views += 1
        article.save(update_fields=['total_views'])
    #将markdown语法渲染成html样式
    md = markdown.Markdown(extensions=[
        #包含 缩写、表格等常用扩展
        'markdown.extensions.extra',
        #语法高亮扩展
        'markdown.extensions.codehilite',
        #目录扩展
        'markdown.extensions.toc',
    ])
    article.body = md.convert(article.body)
    #新增md.toc对象
    #需要传送给模板对象
    #引入评论表单
    comment_form = CommentForm()
    context = {'article': article, 'toc':md.toc, 'comments':comments,'comment_form':comment_form,}
    #载入模板，返回context对象
    return render(request, 'article/detail.html', context)
#检查登录
@login_required(login_url='/userprofile/login/')
#设置只有超级管理员才能写文章
@permission_required('raise_excepthon',login_url='/userprofile/login/')
#写文章
def article_create(request):
    #判断用户是否提交数据
    if request.method == "POST":
        #增加request.FILES
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        #将提交的数据赋值到表单实列中
        # article_post_form = ArticlePostForm(data=request.POST)
        #判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            #保存数据，暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            #指定数据库中 id=1 的用户为作者
            #new_article.author = User.objects.get(id=1)
            #如果进行过删除表的操作，可能找不到id=1的用户
            #此时请重写创建用户，并传入此用户的id
            #指定目前登录的用户为作者 
            new_article.author = User.objects.get(id=request.user.id)
            # 新增的代码
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            #将新文章保存到数据库中
            new_article.save()
            # 新增代码，保存 tags 的多对多关系
            article_post_form.save_m2m()
            #完成后返回到文章列表
            return redirect("article:article_list")
        #如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    #如果用户请求获取数据
    else:
        #创建表单类实例
        article_post_form = ArticlePostForm()
        #文章栏目
        columns = ArticleColumn.objects.all()
        #幅值上下文
        context = { 'article_post_form':article_post_form ,'columns':columns}
        #返回模板
        return render(request, 'article/create.html', context)

#删除文章
# def article_delete(request, id):
#     #根据ID获取需要删除的文章
#     article = ArticlePost.objects.get(id=id)
#     #调用delete()方法删除文章
#     article.delete()
#     #删除后返回文章列表
#     return redirect("article:article_list")

# 提醒用户登录
@login_required(login_url='/userprofile/login/')
# 安全删除文章
def article_safe_delete(request, id):
    article = ArticlePost.objects.get(id=id)
    # 过滤非作者的用户
    if request.user != article.author:
        return HttpResponse("抱歉，你无权删除这篇文章。")
    if request.method == 'POST': 
        article.delete()
        return redirect("article:article_list")          
    else:
        return HttpResponse("仅允许post请求")
# 提醒用户登录
@login_required(login_url='/userprofile/login/')
#更新文章
def article_update(request, id):
    """
    更新文章的视图函数
    通过POST方法提交表单，更新titile、body字段
    GET方法进入初始表单页面
    id： 文章的 id
    """
    #获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id=id)
    #过滤非作者用户
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章")
    #判断用户是否为POST提交表单数据
    if request.method =="POST":
        #将提交的数据赋值到表单实例去中
        article_post_form = ArticlePostForm(data=request.POST)
        #判断提交的数据是否满足数据模型的要求
        if article_post_form.is_valid():
             # 新增的代码
            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            article.title = request.POST['title']
            article.body = request.POST['body']
            article.save()
            #完成后返回修改后的文章，需要传入文章的id值
            return redirect('article:article_detail', id=id)
        #如果数据不合法，返回错误信息
        else:
            return HttpResponse("输入内容有误，请重新输入。")
    
    #如果用户GET请求获取数据
    else:
        # 新增及修改的代码
        columns = ArticleColumn.objects.all()
        #创建表单类实例
        article_post_form = ArticlePostForm()
        #幅值上下文，将article文章对象也传递进去，以便提取旧的内容
        context = { 'article':article, 
                    'article_post_form':article_post_form,
                    'columns':columns,            
        }
        #将响应返回到模板中
        return render(request, 'article/update.html', context)
    

#搜索博客文章
def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    # 用户搜索逻辑
    if search:
        if order == 'total_views':
            # 用 Q对象 进行联合搜索
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            ).order_by('-total_views')
        else:
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            )
    else:
        # 将 search 参数重置为空
        search = ''
        if order == 'total_views':
            article_list = ArticlePost.objects.all().order_by('-total_views')
        else:
            article_list = ArticlePost.objects.all()

    paginator = Paginator(article_list, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    # 增加 search 到 context
    context = { 'articles': articles, 'order': order, 'search': search }

    return render(request, 'article/list.html', context)

