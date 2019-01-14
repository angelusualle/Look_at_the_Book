# -*- coding: utf-8 -*-

import logging
import feedparser
import json

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective
from ask_sdk_model.ui import SimpleCard

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
FEED_URL = 'http://feed.desiringgod.org/look-at-the-book.rss'


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    feed = feedparser.parse(FEED_URL)
    speech_text = "Which of the following most recent episodes would you like to" \
                  " see? Press it or say 'play the first one'"
    reprompt= "Which of the following episodes would you like to see? You can say play number 0 or click on screen."
    return handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token='APL-Template-LAB',
                document=_load_apl_document('lab_start_page.json'),
                datasources={
                            "episodes": {
                                "type": "list",
                                "listId": "bt3Sample",
                                "totalNumberOfItems": 50,
                                "items": [{"title":x['title']} for x in feed['items']]
                            }})).speak(speech_text).ask(reprompt).response


@sb.request_handler(can_handle_func=lambda handler_input:
                    is_request_type("Alexa.Presentation.APL.UserEvent") and
                    len(handler_input.request_envelope.request.to_dict().get('arguments', [])) > 1 and
                    handler_input.request_envelope.request.to_dict()['arguments'][1] == 'episode_selected')
def lab_selected_handler_vui(handler_input):
    selected_index = int(handler_input.request_envelope.request.to_dict()['arguments'][0])
    return play_episode_at_index(selected_index, handler_input)


@sb.request_handler(can_handle_func=is_intent_name("PlayLatestIntent"))
def lab_selected_handler_vui(handler_input):
    return play_episode_at_index(0, handler_input)


@sb.request_handler(can_handle_func=lambda handler_input:
                    is_request_type("Alexa.Presentation.APL.UserEvent") and
                    len(handler_input.request_envelope.request.to_dict().get('arguments', [])) > 1 and
                    handler_input.request_envelope.request.to_dict()['arguments'][0] == 'pause_play_pressed')
def lab_play_pause_handler(handler_input):
    handler_input.attributes_manager.session_attributes['PLAYING'] = handler_input.request_envelope.request.to_dict()['arguments'][1]
    return handler_input.response_builder.speak('').set_should_end_session(False).response


@sb.global_request_interceptor()
def process_request(handler_input):
    """Log the alexa requests."""
    logger.debug("Alexa Request: {}".format(
        handler_input.request_envelope.request))


@sb.global_response_interceptor()
def process_response(handler_input, response):
    logger.debug("Alexa Response: {}".format(response))


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    speech_text = "You can say hello to me!"

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(
            "Hello World", speech_text)).response


@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    speech_text = "Goodbye!"

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Hello World", speech_text)).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    speech = (
        "The Hello World skill can't help you with that.  "
        "You can say hello!!")
    reprompt = "You can say hello!!"
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    logger.error(exception, exc_info=True)

    speech = "Sorry, there was some problem. Please try again!!"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


def _load_apl_document(file_path):
    """Load the apl json document at the path into a dict object."""
    with open(file_path) as f:
        return json.load(f)


def play_episode_at_index(selected_index, handler_input):
    """
    Builds response for playing episode at specific index
    :param selected_index: index of episode in RSS Reader
    :param handler_input: handler_input for request
    :return: response for skill
    """
    episode = [{'title': x['title'], 'URL': x['media_content'][0]['url']} for x in feedparser.parse(FEED_URL)['items']][
            selected_index]
    speech_text = "Playing episode titled: " + episode['title']
    handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token='APL-Template-LAB-2',
                document=_load_apl_document('lab_selection.json'),
                datasources={
                  "episode": {
                      "type": "object",
                      "objectId": "bt3Sample",
                      "info": episode
                  }
                })).speak(speech_text).set_should_end_session(False)
    return handler_input.response_builder.response


handler = sb.lambda_handler()
