from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import json

# Create your models here.
class Antibody(models.Model):
    id_db=models.TextField(null=True, blank=True)
    name=models.CharField(max_length=255)
    date = models.IntegerField(null=True, blank=True) 
    paper=models.TextField()
    reference=models.TextField()
    doi=models.URLField()
    format=models.TextField(null=True, blank=True)
    other_id=models.TextField(null=True, blank=True)
    organism=models.TextField(null=True, blank=True)
    sequence=models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class AntibodyProperty(models.Model):
    antibody = models.ForeignKey(Antibody, on_delete=models.CASCADE, related_name='property_list')
    property_name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    assay = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.property_name}: {self.value}"