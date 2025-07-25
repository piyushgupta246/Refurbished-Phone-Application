# inventory/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Home page
    path('', views.HomeView.as_view(), name='home'),
    path('features/', views.FeatureView.as_view(), name='features'),
    # Phone URLs
    path('phones/', views.PhoneListView.as_view(), name='phone_list'),
    path('phones/<int:pk>/', views.PhoneDetailView.as_view(), name='phone_detail'),
    path('phones/add/', views.PhoneCreateView.as_view(), name='phone_add'),
    path('phones/<int:pk>/edit/', views.PhoneUpdateView.as_view(), name='phone_edit'),
    path('phones/<int:pk>/delete/', views.PhoneDeleteView.as_view(), name='phone_delete'),

    # Brand URLs
    path('brands/add/', views.BrandCreateView.as_view(), name='brand_add'),
    path('brands/<int:pk>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/<int:brand_pk>/add_phone/', views.PhoneCreateView.as_view(), name='phone_add_for_brand'),

    # Listing URLs
    path('phones/<int:phone_pk>/list/', views.create_or_update_listing, name='create_or_update_listing'),
    path('listings/<int:listing_pk>/delist/', views.delist_phone, name='delist_phone'),

    # Order URLs
    path('phones/<int:phone_pk>/order/', views.create_order, name='create_order'),

    # Chatbot URL
    path('submit_query/', views.submit_query, name='submit_query'),

    # Query URLs
    path('queries/', views.QueryListView.as_view(), name='query_list'),
    path('queries/<int:pk>/delete/', views.QueryDeleteView.as_view(), name='query_delete'),

    # Sell New Model URL
    path('sell-new-model/', views.sell_new_model, name='sell_new_model'),

    # Review URL
    path('phones/<int:pk>/review/', views.add_review, name='add_review'),

    # Cart URLs
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
]
