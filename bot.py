from datetime import datetime, timedelta
import asyncio

"""
'bot.py' gör allting timer-relaterat.
När en timer skapas initieras ett objekt av TimeKeeper klassen.
För att initera behövs ett tidsformat i form av en sträng.
Den här klassen hanterar funktionaliteten bakom chatt-kommandon
som exempelvis förlänga pauser, räkna ut återstående tid, mm..
"""


class TimeKeeper:
    def __init__(self, end_time: str):
        self.end_time_string = end_time
        self.end_time_object = self.convert_to_datetime_object()
        self.notification_time = self.calculate_notification_time()
        self.break_length = self.calculate_minutes_remaining()
        self.notification_sent = False
        self.is_lunch_break = False

    def debug_master(self):
        print(
            f"end_time_string: {self.end_time_string}\n"
            f"end_time_object: {self.end_time_object}\n"
            f"break_length: {self.break_length}\n"
            f"notification_time: {self.notification_time}\n"
            f"notification_sent: {self.notification_sent}\n"
            f"lunch_break: {self.is_lunch_break}\n"
        )

    def time_in_future(self) -> bool:
        if self.end_time_object > datetime.now():
            return True

    def convert_to_datetime_object(self) -> datetime:
        time_object = datetime.strptime(self.end_time_string, "%H:%M").time()
        return datetime.combine(datetime.now().date(), time_object)

    def convert_to_string(self) -> str:
        return self.end_time_object.strftime("%H:%M")

    def calculate_notification_time(self) -> datetime:
        return self.end_time_object - timedelta(minutes=10)


    def calculate_minutes_remaining(self) -> int:
        now = datetime.now()
        remaining = self.end_time_object - now
        return max(0, int(remaining.total_seconds() / 60))


    def extend_break(self, minutes):
        self.end_time_object += timedelta(minutes=minutes)
        self.end_time_string = self.convert_to_string()
        self.notification_time += timedelta(minutes=minutes)
        

    async def start_timer(self, notify_callback, time_up_callback):
        if self.break_length >= 59: # Just in case
            self.is_lunch_break = True
        try:
            while datetime.now() < self.end_time_object:
                await asyncio.sleep(10) # Probbably doesnt need to be this frequent
                if datetime.now() >= self.notification_time:
                    if not self.notification_sent:
                        await notify_callback(self.calculate_minutes_remaining())
                        self.notification_sent = True
                if datetime.now() >= self.end_time_object:
                    await time_up_callback()
                    break
        except Exception as e:
            print(f"Error in timer loop: {e}")

    def stop_timer(self):
        pass
