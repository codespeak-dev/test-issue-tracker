from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.urls import reverse
import markdown


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication without password"""
    
    def create_user(self, email, name, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_unusable_password()  # No password needed
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, **extra_fields)


class User(AbstractBaseUser):
    """Custom user model for email-based authentication"""
    
    email = models.EmailField(unique=True, max_length=254)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    def __str__(self):
        return self.name
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser


class Status(models.Model):
    """Issue status model"""
    
    name = models.CharField(max_length=50, unique=True)
    is_open = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Statuses"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag model for categorizing issues"""
    
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')  # Hex color code
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class IssueManager(models.Manager):
    """Custom manager for Issue model to handle soft deletes"""
    
    def get_queryset(self):
        """Return only non-deleted issues by default"""
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def with_deleted(self):
        """Return all issues including deleted ones"""
        return super().get_queryset()
    
    def deleted_only(self):
        """Return only deleted issues"""
        return super().get_queryset().filter(deleted_at__isnull=False)


class Issue(models.Model):
    """Issue model"""
    
    summary = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='issues')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_issues')
    assignee = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_issues'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='issues')
    slack_thread_ts = models.CharField(max_length=50, blank=True, null=True, help_text="Slack thread timestamp for notifications")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when issue was deleted (null = not deleted)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = IssueManager()
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        prefix = "[DELETED] " if self.deleted_at else ""
        return f"{prefix}{self.summary}"
    
    def get_absolute_url(self):
        return reverse('issue_detail', args=[self.id])
    
    def description_html(self):
        """Convert markdown description to HTML"""
        return markdown.markdown(self.description, safe_mode='escape')
    
    def is_deleted(self):
        """Check if issue is deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Soft delete the issue"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    def restore(self):
        """Restore a soft-deleted issue"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])


class Comment(models.Model):
    """Comment model"""
    
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.author.name} on {self.issue.summary}'
    
    def content_html(self):
        """Convert markdown content to HTML"""
        return markdown.markdown(self.content, safe_mode='escape')


class IssueEditHistory(models.Model):
    """Track issue edit history"""
    
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='edit_history')
    editor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issue_edits')
    field_name = models.CharField(max_length=100, help_text="Name of the field that was edited")
    old_value = models.TextField(blank=True, help_text="Previous value of the field")
    new_value = models.TextField(blank=True, help_text="New value of the field")
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-edited_at']
    
    def __str__(self):
        return f'{self.editor.name} edited {self.field_name} on {self.issue.summary}'


class Settings(models.Model):
    """Application settings model (singleton)"""
    
    slack_bot_token = models.CharField(max_length=200, blank=True)
    slack_channel_id = models.CharField(max_length=100, blank=True)
    github_access_token = models.CharField(max_length=200, blank=True)
    github_repository_owner = models.CharField(max_length=100, blank=True)
    github_repository_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name_plural = "Settings"
    
    def __str__(self):
        return 'Application Settings'
    
    def save(self, *args, **kwargs):
        """Singleton pattern - only allow one instance"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of settings"""
        pass
    
    @classmethod
    def load(cls):
        """Get or create the settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj