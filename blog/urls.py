from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


app_name='blog'
urlpatterns = [
    path('', views.index, name='index'),
    path('antibody_search/', views.antibody_search, name='antibody_search'),
    path('about/', views.about, name='about'),
    path('paper/', views.paper, name='paper'),
    path('help/', views.help, name='help'),
    path('contact/', views.contact, name='contact'),
    path('antibody/<str:id_db>', views.antibody_detail, name='antibody_detail'),
    path('download/<str:id_db>/', views.download_all, name='download_all'),
    path('downloadsequence/<str:id_db>', views.download_sequence, name='download_sequence'),
    path('check_pdb/<str:id_db>/', views.check_pdb),
    path('sequence_similarity/',views.sequence_similarity, name='sequence_similarity',)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
