from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from aiohttp import web
from chat import ChatHandler
import os
import logging

# Please Bill..

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ID = os.environ.get("teams_breakbot_ID")
APP_PASSWORD = os.environ.get("teams_breakbot_SECRET")
TENANT_ID = os.environ.get("TENANT_ID")

if not APP_ID or not APP_PASSWORD:
    logger.error("MISSING ENVIRONMENT VARIABLES.")

SETTINGS = BotFrameworkAdapterSettings(
    APP_ID,
    APP_PASSWORD,
    channel_auth_tenant=TENANT_ID
)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = ChatHandler()

async def messages(req: web.Request) -> web.Response:
    logger.info("RECIEVED A MESSAGE")

    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
        logger.info(f"RECIEVED BODY: {body}")
    else:
        logger.warning("RECIEVED NON-JSON CONTENT.")
        return web.Response(status=415)
    
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else""
    logger.info("PROCESSING ACTIVITY")

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    logger.info("ACTIVITY PROCESSED")

    if response:
        logger.info(f"SENDING RESPONSE: {response.body}")
        return web.json_response(data=response.body, status=response.status)
    
    logger.info("NO RESPONSE TO SEND")
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
    