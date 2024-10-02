from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from aiohttp import web
from chat import ChatHandler
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ID = os.environ.get("teams_breakbot_ID")
APP_PASSWORD = os.environ.get("teams_breakbot_SECRET")

if not APP_ID or not APP_PASSWORD:
    logger.error("MISSING ENVIRONMENT VARIABLES.")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = ChatHandler()

async def messages(req: web.Request) -> web.Response:
    logger.info("Recieved a message...")
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
        logger.info("STARTING APPLICATION")
        web.run_app(APP, port=8000)
    except Exception as e:
        print(f"Error with: {e}")
        logger.error(f"ERROR STARTING APPLICATION: {e}")
        raise e
    