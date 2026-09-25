from django.urls import path

from .views import ListOrdersView, DetailOrderView

urlpatterns = [
    path('orders', ListOrdersView.as_view(), name='order-list'),
    path('orders/<int:id>', DetailOrderView.as_view(), name='order-details')
]
