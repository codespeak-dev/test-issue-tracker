from django.db import models
from django.urls import reverse
from django.conf import settings


class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_open = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'statuses'
        db_table = 'issues_status'

    def __str__(self):
        return self.name


class Issue(models.Model):
    summary = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_issues'
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        db_table = 'issues_issue'
        indexes = [
            models.Index(fields=['status', '-updated_at']),
        ]

    def __str__(self):
        return self.summary

    def get_absolute_url(self):
        return reverse('issues:detail', kwargs={'pk': self.pk})


class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        db_table = 'issues_comment'
        indexes = [
            models.Index(fields=['issue', 'created_at']),
        ]

    def __str__(self):
        return f'Comment by {self.author.name} on {self.issue.summary}'
