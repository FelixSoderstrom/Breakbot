from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from aiohttp import web
from chat import ChatHandler
import os
"""
"""

APP_ID = os.environ["teams_breakbot_ID"]
APP_PASSWORD = os.environ["teams_breakbot_SECRET"]
# APP_ID = ""
# APP_PASSWORD = ""
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = ChatHandler()

async def messages(req: web.Request) -> web.Response:
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return web.Response(status=415)
    
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else""
    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=201)

APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP)
    except Exception as e:
        print(f"Error with: {e}")
        raise e