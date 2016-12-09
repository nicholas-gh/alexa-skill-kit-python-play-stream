from __future__ import print_function

import fuzzy

import logging
import difflib

logger = logging.getLogger()
logger.setLevel(logging.INFO)

listen_key = 'xxxxxxxxx'

# we proxy via cloudfront to make an HTTPS server, as AudioPlayer requires HTTPS
domain = 'xxxxxx.cloudfront.net'

soundex = fuzzy.nysiis

# removed this from the example - it's a mapping between channel
# friendly name and the stream HTTP endpoint
channels = {}

images = {}

sound_mapping = {}
for channel in channels.keys():
    sound_mapping[soundex(channel)] = channel
      
def build_directives(url=None, token=None):
    if url:
        directives = [{
        "type": "AudioPlayer.Play",
        "playBehavior": "REPLACE_ALL",
        "audioItem": {
          "stream": {
            "token": token,
            #"expectedPreviousToken": None,
            "url": url,
            "offsetInMilliseconds": 0
          }
         }
        }]
    else:
        directives = [{"type": "AudioPlayer.Stop"}]
    return directives
    
def build_speechlet_response(title, output, reprompt_text, should_end_session, url=None, token=None):
    if title and output:
        if token in images:
            card = {
                'type': 'Simple',
                'title': "Music - " + title,
                'content': output
            }
        else:
            card = {
                'type': 'Simple',
                'title': "Music - " + title,
                'content': "Music - " + output
            }
    else:
        card = {}
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': card,
        #'reprompt': {
        #   'outputSpeech': {
        #        'type': 'PlainText',
        #       'text': None
        #    }
        #},
        'directives': build_directives(url, token),
        'shouldEndSession': should_end_session
    }
    

def build_response(session_attributes, speechlet_response):
    resp = {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response}
    logger.info(repr(resp))
    return resp

def build_audioplayer_response(session_attributes, directives):
    resp = {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': {'directives': directives}
        }
    logger.info(repr(resp))
    return resp

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to xxxxxxxxx. You can play the following channels: "
    speech_output = speech_output + ", ".join(sorted(channels.keys()))
    speech_output = speech_output + ". Which channel would you like?"
    
    # (Not actually used)
    reprompt_text = "Please say which xxxxxxxxxxx channel you would like."
    
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you listening. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))
      
def play(intent, session):
    session_attributes = {}
    reprompt_text = None
    filename = None
    url = None

    if 'Channel' in intent['slots']:
        channel = intent['slots']['Channel']['value']
        sex = soundex(channel)
        match = difflib.get_close_matches(sex, sound_mapping.keys(), 1)[0]
        logger.info("Alexa heard %s, soundex is %s (map is %s), match is %s",
                    channel,
                    sex,
                    repr(sound_mapping),
                    match)
        try:
            filename = channels[sound_mapping[match]]
            url = 'https://{}/{}?{}'.format(domain, filename, listen_key)
            speech_output = "Now playing " + sound_mapping[match]
        except KeyError:
            speech_output = "I couldn't find channel {}".format(channel)
        should_end_session = True
    else:
        speech_output = "I'm not sure which channel you wanted."
        should_end_session = False


    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session, 
        url, filename))

def pause(intent):
    session_attributes = {}
    return build_audioplayer_response(session_attributes, build_directives())

def resume(intent, context):
    session_attributes = {}
    url = None
    filename = None

    if 'AudioPlayer' in context and 'token' in context['AudioPlayer']: 
        url = 'https://{}/{}?{}'.format(domain, context['AudioPlayer']['token'], listen_key)

    return build_audioplayer_response(session_attributes, build_directives(url, token=context['AudioPlayer']['token']))

def playnext(intent, context, offset=1):
    session_attributes = {}
    url = None
    filename = None

    if 'AudioPlayer' in context and 'token' in context['AudioPlayer']:
        current = context['AudioPlayer']['token']
        for k, v in channels.items():
            if v == current:
                sorted_channels = list(sorted(channels))
                new_token = channels[sorted_channels[(sorted_channels.index(k)+offset) % len(sorted_channels)]]
        url = 'https://{}/{}?{}'.format(domain, new_token, listen_key)

    return build_audioplayer_response(session_attributes, build_directives(url, token=context['AudioPlayer']['token']))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

    logger.info(repr(session_started_request))
    logger.info(repr(session))

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    logger.info(repr(launch_request))
    logger.info(repr(session))
    return get_welcome_response()


def on_intent(intent_request, session, context):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
          
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    print(intent_name)
    logger.info(repr(intent_request))
    logger.info(repr(session))
    
    # Dispatch to your skill's intent handlers
    if intent_name == "xxxxxxxxxxxxx":
        return play(intent, session)
    elif intent_name == "AMAZON.PauseIntent":
        return pause(intent)
    elif intent_name == "AMAZON.ResumeIntent":
        return resume(intent, context)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here
    logger.info(repr(session_ended_request))
    logger.info(repr(session))

# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    logger.info(repr(event))
    if 'session' in event:
          print("event.session.application.applicationId=" + event['session']['application']['applicationId'])

    #logger.info(repr(dir(context)))

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if 'session' in event and event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'], event['context'])
    elif event['request']['type'] == "PlaybackController.PauseCommandIssued":
        return pause(event['request'])
    elif event['request']['type'] == "PlaybackController.PlayCommandIssued":
        return resume(event['request'], event['context'])
    elif event['request']['type'] == "PlaybackController.NextCommandIssued":
        return playnext(event['request'], event['context'], 1)
    elif event['request']['type'] == "PlaybackController.PreviousCommandIssued":
        return playnext(event['request'], event['context'], -1)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
    elif event['request']['type'] == "AudioPlayer.PlaybackStarted":
        pass
