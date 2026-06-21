from django.db import models
from django.urls import reverse


class ServiceCategory(models.Model):
    """Categories of services that experts can provide."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, default='fa-solid fa-user', 
                                   help_text='Font Awesome icon class')
    color = models.CharField(max_length=7, default='#2563EB', 
                             help_text='Hex color code for the category')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Service Categories'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('expert_list_by_category', kwargs={'category_slug': self.slug})
    
    @property
    def color_with_alpha(self):
        """Return the category hex color with a low alpha suffix for light backgrounds."""
        return f"{self.color}20"
    
    def get_icon_html(self):
        return f'<i class="{self.icon_class}"></i>'
