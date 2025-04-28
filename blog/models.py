from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import json

# Create your models here.
class Antibody(models.Model):
    id_db=models.TextField(null=True, blank=True)
    name=models.CharField(max_length=255)
    date = models.IntegerField(null=True, blank=True) 
    reference=models.TextField()
    doi=models.URLField()
    sequence=models.JSONField(null=True, blank=True)
    properties=models.JSONField(default=dict,null=True, blank=True)
    property_keys = models.TextField(null=True, blank=True)  # 存储所有性质键名
    
    def get_properties(self):
        return json.load(self.properties)
    
    def save(self, *args, **kwargs):
        # 自动提取 properties 的键名，存储到 property_keys 中
        
        if self.properties:
            self.property_keys = ", ".join(self.properties.keys())
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
