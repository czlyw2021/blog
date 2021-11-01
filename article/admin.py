from django.contrib import admin

#导入ArticlePost
from .models import ArticleColumn, ArticlePost

#注册
admin.site.register(ArticlePost)
#注册文章栏目
admin.site.register(ArticleColumn)