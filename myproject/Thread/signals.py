from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Like, Comment, Posting

# Cập nhật số Like/Dislike khi có sự kiện thêm hoặc xóa Like
@receiver(post_save, sender=Like)
@receiver(post_delete, sender=Like)
def update_like_dislike_count(sender, instance, **kwargs):
    content_object = instance.ContentObject
    if isinstance(content_object, Posting) or isinstance(content_object, Comment):
        like_count = content_object.likes.filter(Type="Like").count()
        dislike_count = content_object.likes.filter(Type="Dislike").count()

        content_object.LikeCount = like_count
        content_object.DislikeCount = dislike_count
        content_object.save()

# Cập nhật số Comment khi có sự kiện thêm hoặc xóa Comment
@receiver(post_save, sender=Comment)
@receiver(post_delete, sender=Comment)
def update_comment_count(sender, instance, **kwargs):
    content_object = instance.ContentObject
    if isinstance(content_object, Posting):
        comment_count = content_object.comments.count()
        content_object.CommentCount = comment_count
        content_object.save()
