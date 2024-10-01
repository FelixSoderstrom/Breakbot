from botbuilder.core import ActivityHandler, TurnContext
from random import choice
import re
import asyncio
from bot import TimeKeeper

"""
'chat.py' gör allting chatt-relaterat.
Läser av inkommande meddelanden, letar efter specifika mönster och exekverar kod därefter.
Hanterar errors gällande user input.
Skickar meddelanden till chatten.
När ett visst möster detekterats i ett meddelande initierar vi 'TimeKeeper' från 'bot.py'.
Allt timer-relaterat hittar du i 'bot.py'.

Hade varit coolt att koppla ihop denna bot med Björns discord-bot så att man kan
skicka kommandon till den ena men få notifikationer i båda.
Detta skulle kräva en metod som lyssnar efter discord-botten.
Osäker på om den metoden/funktionen hamnar här eller i main.


Issues:

"""


class ChatHandler(ActivityHandler):
    def __init__(self):
        self.current_break = None
        self.turn_context = None
        """
        Använd sender_id istället för sender_name
        om du kan skaffa access till användarnas id.

        self.authorized_users = [
            {"Tobias Fors": 12345678990},
            {"Amanda Mårtensson": 1234567890},
            {"Felix Söderström": 1234567890}
        ]

        Jag har inte clearence. Ouch..
        """
        self.authorized_users = [
            "User" # For BotFrameworkEmulator
            ]


    async def on_message_activity(self, turn_context=TurnContext):
        """
        Läser igenom alla meddelanden och väljer vilka som ska processeras.
        """
        self.turn_context = turn_context
        sender_name = self.turn_context.activity.from_property.name
        message_text = self.turn_context.activity.text
        command = self.extract_command(message_text)

        package = {
            "sender_name": sender_name,
            "command": command,
            "message_text": message_text
        }
        command_methods = {
            "tillbaka": self.set_break,
            "extend": self.extend_break,
            "current": self.current_break_delta,
            "help": self.help,
            "stop": self.cancel_break
        }
        if command:
            await command_methods[command](package)


    async def send(self, bot_message):
        """
        Skickar meddelanden till chatten.
        """
        try:
            await self.turn_context.send_activity(bot_message)
        except TypeError as e:
            print(f"Dog don't bark: {e}  \nMessage: {bot_message}")


    async def no_active_break(self):
        await self.send("Ingen paus är aktiv just nu.")


    def is_authorized_user(self, sender_name) -> bool:
        return sender_name in self.authorized_users
    


    async def notify_callback(self, minutes):
        """
        Skickar ut ett meddelande när det är 5 minuter kvar.
        """
        prompts = [
            "Fyll på med kaffe.",
            "Gör era toalettbesök.",
            "Hörru! Inte sova..",
            "Hallå? HALLÅ!",
            "Slingra er tillbaka. Get it?",
            "Stäng ner TikTok!",
            "Jag gör bara mitt jobb..",
            "Lorem Ipsum?",
            "Kontorstolen är försummad.",
            "Enligt min klocka är det snart dags att vara vuxen igen.",
            "Ryck upp dig själv nu..",
            "Varning: Ansvar lurar bakom nästa hörn.",
            "Gör dig redo för att återförenas med herr IndentationError.",
            "Dags att byta från break till continue.",
        ]
        if self.current_break.is_lunch_break:
            await self.send(choice(prompts))
        await self.send(f"Vi kör igång om {minutes} minuter.")


    async def time_up_callback(self):
        """
        Skickar ut ett meddelande när tiden är slut.
        Tar bort den aktuella timern.
        """
        await self.send(
            f"Klockan är {self.current_break.end_time_string}.  \n"
            "Pausen är nu slut."
        )
        self.current_break = None


    async def set_break(self, package):
        """
        Startar en ny paus genom att initiera TimeKeeper klassen.
        Endast Tobias och Amanda kommer in här.
        """
        sender_name = package["sender_name"]
        message_text = package["message_text"]

        if self.is_authorized_user(sender_name):
            if not self.current_break:
                end_time = self.extract_timestamp(message_text)
                self.current_break = TimeKeeper(end_time)
                if self.current_break.time_in_future():
                    # Om vi vill connecta med Björns discord-bot så är det här vi skickar info till honom
                    asyncio.create_task(
                        self.current_break.start_timer(
                            self.notify_callback, self.time_up_callback
                        )
                    )
                    await self.send(
                        "Pausen har börjat.  \n"
                        f"Kom tillbaka klockan "
                        f"{self.current_break.end_time_string}"           
                    )
                else:
                    await self.send(
                        "Vi behöver fler frameworks för åstadkomma det du ber om.  \n"
                        "Ange en tid i framtiden istället."
                    )
                    self.current_break = None
            else:
                await self.no_active_break()
                await self.send("Använd '!extend' om du vill förlänga pausen.")
        else:
            await self.send(
                f"Tyvärr, {sender_name}. Rollen som 'rast-ansvarig' "
                "är redan tillsatt.  \nMen skicka gärna din ansökan till "
                "'skräppost@teknikhögskolan.se' så hör vi av oss "
                "till dig inom 'NaN' arbetsdagar."
            )


    async def extend_break(self, package):
        """
        Förlänger den nuvarande pausen, om den finns.
        Endast Tobias kommer in här.
        """
        sender_name = package["sender_name"]
        message_text = package["message_text"]

        if self.current_break is None:
            await self.no_active_break()
        if self.is_authorized_user(sender_name):
            minutes = self.extract_minutes(message_text)
            self.current_break.extend_break(minutes)
            await self.send(
                f"Pausen har förlängts med {minutes} minuter.  \n"
                f"Var tillbaka klockan {self.current_break.end_time_string}"
                )
        else:
            await self.send("Du får inte förlänga pauser.")


    async def current_break_delta(self, package):
        """
        Räknar ut hur många minuter som återstår på pausen och meddelar chatten.
        """
        if self.current_break:
            minutes = self.current_break.calculate_minutes_remaining()
            await self.send(
                f"Pausen varar till {self.current_break.end_time_string}.  \n"
                f"Det är om {minutes} minuter."
            )
        else:
            await self.no_active_break()


    async def help(self, package):
        """
        Skickar ut ett hjälp-meddelande.
        """
        help_text = (
            "!current - Visar status på den nuvarande pausen.  \n"
            "!tillbaka (tid) - Startar en ny paus. Tidsformat: 09.00, 09:00, 0900  \n"
            "!extend (minuter) - Förläng den nuvarande pausen.  \n"
            "!stop - Avbryter den nuvarande rasten."
        )
        await self.send(help_text)


    async def cancel_break(self, package):
        sender_name = package["sender_name"]
        if self.is_authorized_user(sender_name):
            if self.current_break:
                await self.send(f"Pausen avbröts av {sender_name}")
                self.current_break = None
            else:
                await self.no_active_break()
        else:
            await self.send("Du har inte behörighet att avbryta pauser.")


    def extract_command(self, chat_message) -> str:
        """
        Extraherar kommandot från meddelandet och returnerar det
        för enklare och tydligare hantering i 'on_message_activity'.
        """
        commands = {
            "!tillbaka": "tillbaka",
            "!extend": "extend",
            "!current": "current",
            "!help": "help",
            "!stop": "stop",
        }
        lower_message = chat_message.lower()
        for command, action in commands.items():
            if lower_message.startswith(command):
                return action


    def extract_timestamp(self, chat_message) -> str:
        """
        Extraherar tidsformatet från meddelandet och 
        returnerar det uniformt formatterat: 'HH:MM'
        Metoden bara hamnade här men den passar bättre
        i TimeKeeper klassen med all annan funktionalitet.
        """
        pattern = r"(\d{1,2}[:.]?\d{2})"  # '09.00', '09:00' '0900'
        match = re.search(pattern, chat_message)
        if match:
            time = match.group(1)
            if ":" in time:
                hours, minutes = time.split(":")
            elif "." in time:
                hours, minutes = time.split(".")
            else:
                hours, minutes = time[:2], time[2:]
            return f"{hours}:{minutes}"


    def extract_minutes(self, message_text) -> str:
        pattern = r"(\d+)" # Any number
        match = re.search(pattern, message_text)
        if match:
            return int(match.group(1))
        return 0
