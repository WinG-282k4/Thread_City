import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

#Account of user
class Account(AbstractUser):  # Kế thừa từ AbstractUser để quản lý tài khoản tốt hơn

    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID làm khóa chính

    Phone = models.CharField(max_length=15, unique=True)  # Giới hạn độ dài số điện thoại
    Address = models.TextField(null=True, blank=True)  # Cho phép để trống
    Avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)  # Lưu ảnh đại diện
    DateOfBirth = models.DateField(null=True, blank=True)

    # Thêm trường đếm số thông báo chưa đọc
    UnreadNotificationCount = models.IntegerField(default=0)

    def __str__(self):
        return self.username  # Hiển thị tên tài khoản

    # Followers and Following
    followers = models.ManyToManyField(
        'self',
        through='Follow',
        related_name='following',
        symmetrical=False
    )

# Follow of user
class Follow(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Follower and Following
    follower = models.ForeignKey(Account, related_name='following_relationships', on_delete=models.CASCADE)
    following = models.ForeignKey(Account, related_name='follower_relationships', on_delete=models.CASCADE)
    
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

# Post of user
class Posting(models.Model):

    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Title = models.CharField(max_length=100)
    Content = models.TextField()
    Image = models.ImageField(upload_to="posts/", null=True, blank=True)
    Author = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="posts")

    # Statistic of post
    LikeCount = models.IntegerField(default=0)
    DislikeCount = models.IntegerField(default=0)
    CommentCount = models.IntegerField(default=0)

    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    # Link like
    Likes = GenericRelation("Like", related_query_name="post_likes")
    Comments = GenericRelation("Comment", related_query_name="post_comments")

    def __str__(self):
        return self.Title

#User comment of post or other comment 
class Comment(models.Model):

    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Content = models.TextField()
    Author = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="comments")

    Parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies") # Post or comment 
    Post = models.ForeignKey(Posting, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    
    LikeCount = models.IntegerField(default=0)
    DislikeCount = models.IntegerField(default=0)

    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    # Link like
    Likes = GenericRelation("Like", related_query_name="comment_likes")

    def __str__(self):
        return self.Content


class Like(models.Model):
    LIKE_CHOICES = (
        ('Like', 'Like'),
        ('Dislike', 'Dislike'),
    )

    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    User = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="likes")

    #like of post or comment 
    ContentType = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    ObjectId = models.UUIDField(db_index=True)  # Thêm index để tối ưu truy vấn
    ContentObject = GenericForeignKey('ContentType', 'ObjectId')

    Type = models.CharField(max_length=7, choices=LIKE_CHOICES)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.User} {self.Type}d {self.ContentObject}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('reply', 'Reply'),
        ('mention', 'Mention'),
        ('follow', 'Follow'),
    )

    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Người nhận thông báo
    Recipient = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='notifications')
    
    # Người tạo ra hành động dẫn đến thông báo
    Actor = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='actions')
    
    # Loại thông báo
    NotificationType = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    
    # Nội dung thông báo
    Message = models.TextField()
    
    # Link đến đối tượng liên quan (post hoặc comment)
    ContentType = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    ObjectId = models.UUIDField(db_index=True)
    ContentObject = GenericForeignKey('ContentType', 'ObjectId')
    
    # Trạng thái đã đọc hay chưa
    IsRead = models.BooleanField(default=False)
    
    CreatedAt = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-CreatedAt']
        indexes = [
            models.Index(fields=['Recipient', 'IsRead', 'CreatedAt']),
        ]

    def __str__(self):
        return f"Notification to {self.Recipient.username}: {self.Message}"

@receiver(post_save, sender=Notification)
def update_notification_count_on_create(sender, instance, created, **kwargs):
    if created:  # Chỉ tăng khi tạo mới thông báo
        recipient = instance.Recipient
        recipient.UnreadNotificationCount += 1
        recipient.save()

@receiver(post_save, sender=Notification)
def update_notification_count_on_read(sender, instance, created, **kwargs):
    if not created:  # Chỉ xử lý khi cập nhật trạng thái đọc
        try:
            old_notification = Notification.objects.get(pk=instance.pk)
            # Khi thông báo chuyển từ chưa đọc sang đã đọc
            if not old_notification.IsRead and instance.IsRead:
                recipient = instance.Recipient
                recipient.UnreadNotificationCount = max(0, recipient.UnreadNotificationCount - 1)
                recipient.save()
        except Notification.DoesNotExist:
            pass
