from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('venues/', views.venue_list, name='venue_list'),   # venue listing with filters & search
    path('venue/<int:pk>/', views.venue_detail, name='venue_detail'),
    path('venue/<int:venue_id>/book/', views.create_booking, name='create_booking'),
    
    # Payment pages
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('payment/<int:booking_id>/qr/', views.generate_payment_qr, name='payment_qr'),   # <-- NEW QR URL
    path('payment/<int:booking_id>/success/', views.payment_success, name='payment_success'),
    path('payment/<int:booking_id>/retry/', views.retry_payment, name='retry_payment'),
    
    # User pages
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel-booking/<int:pk>/', views.cancel_booking, name='cancel_booking'),
    
    # Admin pages
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('confirm-payment/<int:pk>/', views.confirm_payment, name='confirm_payment'),
    path('reject-booking/<int:pk>/', views.reject_booking, name='reject_booking'),
    path('add-venue/', views.add_venue, name='add_venue'),
    path('edit-venue/<int:pk>/', views.edit_venue, name='edit_venue'),
    path('delete-venue/<int:pk>/', views.delete_venue, name='delete_venue'),
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('update-booking/<int:pk>/<str:status>/', views.update_booking_status, name='update_booking_status'),
]