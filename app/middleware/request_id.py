import uuid
from starlette.types import ASGIApp, Receive, Scope, Send

class RequestIdMiddleware:
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        req_id = str(uuid.uuid4())
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name.encode(), req_id.encode()))
                message["headers"] = headers
            await send(message)
        await self.app(scope, receive, send_wrapper)
