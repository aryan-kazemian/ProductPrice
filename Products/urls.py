from django.urls import path
from .views import PriceRecordUploadAPIView

urlpatterns = [
    path('api/upload-price-records/', PriceRecordUploadAPIView.as_view(), name='upload_price_records'),
]
