from django.urls import path
from .views import RegisterView, LoginView, TrainView, BookingView, AnalyticsView, MyBookingsView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('trains/', TrainView.as_view()),
    path('bookings/', BookingView.as_view()),
    path('analytics/top-routes/', AnalyticsView.as_view()),
    path('bookings/my/', MyBookingsView.as_view()),
]