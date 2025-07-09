from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('api/ticket-types/', views.TicketTypeListView.as_view(), name='ticket_type_list'),
    path('api/book-tickets/', views.CreateBookingView.as_view(), name='create_booking'),
    path('sslcommerz/success/', views.sslcommerz_success, name='sslcommerz_success'),
    path('sslcommerz/fail/', views.sslcommerz_fail, name='sslcommerz_fail'),
    path('sslcommerz/cancel/', views.sslcommerz_cancel, name='sslcommerz_cancel'),
    path('sslcommerz/ipn/', views.sslcommerz_ipn, name='sslcommerz_ipn'),
]