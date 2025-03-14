from django.contrib import admin
from .models import Account, Posting, Comment, Like, Notification, Follow

# Register models
admin.site.register(Account)
admin.site.register(Posting)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Notification)
admin.site.register(Follow)