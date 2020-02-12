# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import datetime
import pytz
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BusTime:
    def __init__(self, raw, route):
        self.raw = raw
        self.route = route   # A or AB
        self.dt = None # datetime
        self.td = None # timedelta
        self.sec_delta = None # number of seconds before/later


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> 
        
        tz = pytz.timezone('US/Eastern')
        now = datetime.datetime.now(tz)
    
        if now.weekday() < 5: #0 = Mon, 4 = Fri, 5 = Sat, 6 = Sun
            speak_output = self.get_weekday_response(now)
        else:
            speak_output = self.get_weekend_response(now)

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask(speak_output) # close the prompt
                .response
        )
        
    def get_weekend_response(self, now):
        ab_shuttle_string_times = ["7:15 AM", "8:00 AM", "8:45 AM", "9:30 AM", "10:15 AM", "11:00 AM ", "11:45 AM", "1:30 PM", "2:15 PM", "3:00 PM", "3:45 PM", "4:30 PM", "5:15 PM", "6:00 PM", "7:30 PM", "8:15 PM", "9:00 PM", "9:45 PM", "10:30 PM", "11:15 PM"]
        ab_buses = [BusTime(raw, "A B") for raw in ab_shuttle_string_times]

        return self.process_buses_and_get_response(ab_buses, now)
    
    
    def get_weekday_response(self, now):
        a_shuttle_raw = ["7:15 AM", "7:45 AM", "8:15 AM", "8:45 AM", "9:15 AM", "9:45 AM", "10:15 AM", "10:45 AM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM"]
        ab_shuttle_raw = ["11:15 AM", "12:00 AM", "12:45 AM", "1:30 PM", "2:15 PM", "3:00 PM", "3:45 PM", "6:30 PM", "7:15 PM", "8:00 PM", "8:45 PM", "9:30 PM", "10:15 PM", "11:00 PM", ]
        # watch out, 12:45 PM is bad!
        buses = [BusTime(raw, "A") for raw in a_shuttle_raw] + [BusTime(raw, "A B") for raw in ab_shuttle_raw]
        return self.process_buses_and_get_response(buses, now)
    

    def process_buses_and_get_response(self, buses, now):
        for bus in buses:
            bus.dt = self.convert_string_time_to_dt(bus.raw, now)
            bus.td = bus.dt - now
            bus.sec_delta = bus.td.total_seconds()

        buses.sort(key=lambda x: abs(x.sec_delta))
        return self.compose_answer_from_bustime(buses[1]) + ". " + self.compose_answer_from_bustime(buses[0])


    def convert_string_time_to_dt(self, x, now):
        groups = re.match('(\d+):(\d+) (AM|PM)', x).groups()
        h, m, s = int(groups[0]), int(groups[1]), 0
        if groups[2] == "PM": h += 12

        dt = now.replace(hour=h, minute=m, second=s)
        return dt


    def compose_answer_from_bustime(self, bustime):
        if bustime.sec_delta < 0:
            return "shuttle {} left {} minutes ago".format(bustime.route, round(-bustime.sec_delta / 60))
        else:
            return "shuttle {} will leave in {} minutes".format(bustime.route, round(bustime.sec_delta / 60))


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()