# federated/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from urllib.parse import parse_qs
import jwt
from django.conf import settings
# from .models import FederatedRun, ClientEventLog
import re 
from django.apps import apps
import json 

from asgiref.sync import sync_to_async
# class FederatedConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         print("call was on point")
#         self.user_id = None  # ✅ always define it

#         query_params = parse_qs(self.scope["query_string"].decode())
#         token = query_params.get("token", [None])[0]
#         print("Token:", token)

#         if not token:
#             await self.close(code=4001)
#             return

#         try:
#             payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#             print(payload)
#             raw_user_id = payload.get("user_id")
#             print("Raw user_id:", raw_user_id)

#             if not raw_user_id:
#                 await self.close(code=4002)
#                 return

#             # ✅ sanitize group name
#             self.user_id = str(raw_user_id).strip().replace("-", "_").replace("'", "").replace('"', "")
#             print("Sanitized user_id:", self.user_id)

#         except Exception as e:
#             print("JWT decode error:", e)
#             await self.close(code=4002)
#             return

#         # Add to groups
#         await self.channel_layer.group_add("clients", self.channel_name)
#         await self.channel_layer.group_add(f"client_{self.user_id}", self.channel_name)

#         await self.accept()

#         await self.send_json({
#             "message": "connected",
#             "user_id": self.user_id
#         })

#     async def disconnect(self, code):
#         # ✅ only discard if user_id exists
#         await self.channel_layer.group_discard("clients", self.channel_name)
#         if self.user_id:
#             await self.channel_layer.group_discard(f"client_{self.user_id}", self.channel_name)

#     async def receive_json(self, content):
#         # For now, just echo
#         await self.send_json({
#             "echo": content
#         })

#     async def disconnect(self, code):
#         await self.channel_layer.group_discard("clients", self.channel_name)
#         await self.channel_layer.group_discard(f"client_{self.user_id}", self.channel_name)

#     async def receive_json(self, content):
#         # For now, just echo whatever client sends
#         await self.send_json({
#             "echo": content
#         })


# federated/consumers.py
class FederatedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection attempt")
        from .models import FederatedRun, ClientEventLog
        self.user_id = None  # ✅ always define it
        query_params = parse_qs(self.scope["query_string"].decode())
        token = query_params.get("token", [None])[0]
        if not token:
            await self.close(code=4001)
            return

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            raw_user_id = payload.get("user_id")
            if not raw_user_id:
                await self.close(code=4002)
                return

            # Improved sanitization: normalize, replace invalid chars with _, truncate
            sanitized = str(raw_user_id).strip()
            sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '_', sanitized)  # Only allow valid chars, replace others
            self.user_id = sanitized[:99]  # Ensure <100 chars
            print("Sanitized user_id:", self.user_id)

            # Validate the full group name
            group_name = f"client_{self.user_id}"
            if not self.is_valid_group_name(group_name):
                print(f"Invalid group name: {group_name}")
                await self.close(code=4003)
                return

        except Exception as e:
            print("JWT decode error:", e)
            await self.close(code=4002)
            return

        await self.channel_layer.group_add("clients", self.channel_name)
        await self.channel_layer.group_add(group_name, self.channel_name)

        await self.accept()
        await self.send_json({
            "message": "connected",
            "user_id": self.user_id
        })

    def is_valid_group_name(self, name):
        """Helper to check if name meets Channels requirements."""
        import string
        if not isinstance(name, str) or not name or len(name) >= 100:
            return False
        allowed_chars = set(string.ascii_letters + string.digits + '-_.')
        return all(c in allowed_chars for c in name)


    async def disconnect(self, code):
        await self.channel_layer.group_discard("clients", self.channel_name)
        await self.channel_layer.group_discard(f"client_{self.user_id}", self.channel_name)

    async def receive_json(self, content):
        # Echo from client → server
        await self.send_json({"echo": content})

    async def control_message(self, event):
        """
        Handle admin broadcast messages.
        """
        await self.send_json({
            "type": event["event"],
            "data": event["data"],
        })

    async def federated_message(self, event):
        await self.send(text_data=json.dumps({
            "event": event.get("event"),
            "data": event.get("data"),
        }))

    async def receive_json(self, content):
        """
        Messages from clients (cars).
        Expected format:
        {
            "type": "progress", "data": {"percent": 30}
        }
        """
        msg_type = content.get("type")
        data = content.get("data", {})

        # Save event to DB (sync wrapper)
        await self.log_event(msg_type, data)

        # Echo back acknowledgment
        await self.send_json({
            "ack": msg_type,
            "data": data
        })

    async def log_event(self, event_type, data):
        """
        Save client reports in DB.
        """
        from .models import FederatedRun, ClientEventLog

        @sync_to_async
        def _save_event():
            # Find active run
            run = FederatedRun.objects.filter(is_active=True).order_by("-started_at").first()
            if run:
                ClientEventLog.objects.create(
                    run=run,
                    car_id=self.user_id,
                    event_type=event_type,
                    data=data
                )

        await _save_event()
