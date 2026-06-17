from django.db import models


class Partner(models.Model):
    """Partner organizations for the About page."""

    name = models.CharField(max_length=150)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='partner_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'

    def __str__(self):
        return self.name
