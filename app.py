import os
import settings
import logging
from six.moves import _thread
from flask import Flask, request, Response, json, make_response, render_template
from bot import Bot


from microshiped import ReleaseFlow


bot = Bot()
app = Flask(__name__)
logger = logging.getLogger(__name__)
releaseFlow = ReleaseFlow()
        
class App(object):

    def __init__(self, logger = None):
        super().__init__()
        logger = logger or logging.getLogger(__name__)
        logger.info('app initialized!')
    
    def run(self, debug=False):
        app.run(host='0.0.0.0', port=5000, debug=debug)

def _event_handler(event_type, slack_event):
    '''
    A helper function that routes events from Slack to our Bot
    by event type and subtype.
    Parameters
    ----------
    event_type : str
        type of event recieved from Slack
    slack_event : dict
        JSON response from a Slack event
    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error
    '''
    text = slack_event['event']['text']

    # ================ Message Events =============== #
    # Messages to the bot
    if bot.is_for_me(event_type, slack_event['event']):
        logger.info(f'text is: {text}')
        if text=='!ping':
            logger.info(f'keyword !ping identified.. responding with pong!')
            channel_id = slack_event['event']['channel']
            bot.post_message('Pong!', channel_id)
            return make_response('Message Sent', 200,)
        
        elif text=='!start_release':
            releaseFlow = ReleaseFlow()
            device.on_event('dev_launched_release')
            channel_id = slack_event['event']['channel']
            bot.post_message('Starting release, waiting for QA tests.', channel_id)
            return make_response('Message Sent', 200,)
        elif text=='!tested':
            device.on_event('qa_accepted')
            channel_id = slack_event['event']['channel']
            bot.post_message('Release accepted, waiting for change control approval.', channel_id)
            return make_response('Message Sent', 200,)
        elif text=='!denied':
            device.on_event('qa_denied')
            channel_id = slack_event['event']['channel']
            bot.post_message('Release denied, errors found!', channel_id)
            return make_response('Message Sent', 200,)
        elif text=='!approved':
            device.on_event('cc_accepted')
            channel_id = slack_event['event']['channel']
            bot.post_message('Release approved, waiting to be deployed.', channel_id)
            return make_response('Message Sent', 200,)
        elif text=='!deployed':
            device.on_event('devops_deployed')
            channel_id = slack_event['event']['channel']
            bot.post_message('Release deployed!', channel_id)
            return make_response('Message Sent', 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    # Return a helpful error message
    message = 'You have not added an event handler for the %s' % event_type
    return make_response(message, 200, {'X-Slack-No-Retry': 1}) 

##########################################################
# routes #################################################
@app.route('/', methods=['GET'])
def test():
    logger.info('test called')
    return Response('It works!')

@app.route('/octopus', methods=['POST'])
def octopusEvent():
    logger.info('octopus called')
    content = request.get_json()

    '''start processing octopus deploy events'''
    event = content['Payload']['Event']
    bot.post_octopus_eventMessage(event, settings.SLACK_CHANNEL_ID)

    return Response(), 200

@app.route('/install', methods=['GET'])
def pre_install():
    '''This route renders the installation page with 'Add to Slack' button.'''
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = bot.oauth['client_id']
    scope = bot.oauth['scope']

    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return render_template('install.html', client_id=client_id, scope=scope)

@app.route('/thanks', methods=['GET', 'POST'])
def thanks():
    '''
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    '''
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')

    # The bot's auth method to handles exchanging the code for an OAuth token
    bot.auth(code_arg)

    return render_template('thanks.html')

@app.route('/listening', methods=['GET', 'POST'])
def hears():
    '''
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    '''
    slack_event = json.loads(request.data)

    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    if 'challenge' in slack_event:
        return make_response(slack_event['challenge'], 200, {'content_type': 'application/json'})

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if bot.verification != slack_event.get('token'):
        message = 'Invalid Slack verification token: %s \nReleaseBot has: %s\n\n' % (slack_event['token'], bot.verification)

        # By adding 'X-Slack-No-Retry' : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        make_response(message, 403, {'X-Slack-No-Retry': 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subcribed to
    # Handle the event by event_type and have your bot respond
    if 'event' in slack_event:
        event_type = slack_event['event']['type']
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response('[NO EVENT IN SLACK REQUEST] These are not the droids you\'re looking for.', 404, {'X-Slack-No-Retry': 1})
    