from django.urls import path
from federated.consumers import FederatedConsumer

websocket_urlpatterns = [
    path("ws/federated/", FederatedConsumer.as_asgi()),
]
