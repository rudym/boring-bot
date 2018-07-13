import os, time, random
import settings
import logging
import slackclient
import message
import json

# To remember which teams have authorized your app and what tokens are
# associated with each team, we can store this information in memory on
# as a global object. When your bot is out of development, it's best to
# save this in a more persistant memory store.
authed_teams = {}

class Bot(object):

    def __init__(self, logger = None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info('bot initialized!')

        # Setup some bot metadata
        # These are optional and will overwrite what the slack bot has.
        self.name = settings.BOT_NAME
        self.emoji = settings.BOT_EMOJI

        # When we instantiate a new bot object, we can access the app
        # credentials we set earlier in our local development environment.
        self.oauth = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            # Scopes provide and limit permissions to what our app
            # can access. It's important to use the most restricted
            # scope that your app will need.
            "scope": settings.SCOPE
        }
        self.verification = os.environ.get("VERIFICATION_TOKEN")

        # NOTE: Python-slack requires a client connection to generate
        # an oauth token. We can connect to the client without authenticating
        # by passing an empty string as a token and then reinstantiating the
        # client with a valid OAuth token once we have one.
        self.client = slackclient.SlackClient("")

        # BotId is used to ignore messages from self, will be retrieved
        # automatically once the OAuth token has been retrieved and installed.
        self.botId = ''
    
    ###########################################################
    # skills ##################################################
    def post_message(self, message, channel):
        self.client.api_call(
            'chat.postMessage', 
            channel=channel, 
            text=message, 
            as_user=False
        )

    def post_octopus_eventMessage(self, od_event, channel):

        attachment = self.getOctopusAttachmentMessage(od_event)
        
        self.client.api_call(
            'chat.postMessage', 
            channel=channel, 
            attachments=[attachment]
        )
                    
    ###########################################################
    # some helper methods #####################################
    def get_user_mention(self, user):
        return '<@{user}>'.format(user=user)

    def is_private(self, event):
        return 'channel' in event and event['channel'].startswith('D')

    def is_group(self, event):
        return 'channel' in event and event['channel'].startswith('G')

    def is_channel(self, event):
        return 'channel' in event and event['channel'].startswith('C')

    def is_for_me(self, event_type, event):
        self.logger.info('checking if message is for me')
        
        # check if not my own event
        if event_type == 'message':
            
            # skip if from self
            self.logger.info('is it from myself?')
            if 'user' in event and event['user']==self.botId:
                self.logger.info('event was from myself! skipping..')
                return False

            # in case it is a private message return true
            self.logger.info('is it a private message?')
            if self.is_private(event):
                self.logger.info('yup!')
                return True

            # in case it is a group message return true
            self.logger.info('is it a group message?')
            if self.is_group(event):
                self.logger.info('yup!')
                return True

            # in case it is a channel message return true
            self.logger.info('is it a channel message?')
            if self.is_channel(event):
                self.logger.info('yup!')
                return True

            # in case it is not a private message check mention
            self.logger.info('is it a mention?')
            text = event['text']
            if text and self.get_user_mention(self.botId) in text.strip().split():
                self.logger.info('yup!')
                return True
        
        self.logger.info('nope! skipping..')
        return False
    
    def getPongAttachmentMessage(self):
        return {
            'title': 'Pong!',
            'title_link': 'http://www.pong.com/',
            'text': 'Pong response from ReleaseBot!',
            'color': '#00FF00'
        }

    def getOctopusAttachmentMessage(self, od_event):

        # some vars for the attachment
        category = od_event['Category']
        username = od_event['Username']
        message = od_event['Message']
        
        # extract deploymentId from event data
        relatedDocumentIds = od_event['RelatedDocumentIds']
        deploymentId = ''
        for i, elem in enumerate(relatedDocumentIds):
            if 'Deployments' in elem:
                deploymentId = elem
                break

        # construct release url
        baseUrl = 'http://octopus2.barfoot.co.nz/app#/'
        octopusDeployUrl = f'{baseUrl}deployments/{deploymentId}'

        # set color for each status
        if (category == 'DeploymentStarted'):
            categoryColor = 'warning'
        elif (category == 'DeploymentSucceeded'):
            categoryColor = 'good'
        elif (category == 'DeploymentFailed'):
            categoryColor = 'danger'
        else:
            categoryColor = '#3a2ae7'

        # generate attachment json
        return {
            "fallback": message,
            "color": categoryColor,
            "title": "New release event from Octopus Deploy",
            "text": message,
            "fields": [
                {
                    "title": "Queued By",
                    "value": username,
                    "short": True
                },
                {
                    "title": "Status",
                    "value": category,
                    "short": True
                },
                {
                    "title": "Release Summary",
                    "value": octopusDeployUrl,
                    "short": False
                },
                {
                    "title": "Seq Logs",
                    "value": "https://logging.barfoot.co.nz",
                    "short": False
                },
            ]
        }
                    
    ###########################################################
    # oauth methods ###########################################
    def auth(self, code):
        """
        Authenticate with OAuth and assign correct scopes.
        Save a dictionary of authed team information in memory on the bot
        object.
        Parameters
        ----------
        code : str
            temporary authorization code sent by Slack to be exchanged for an
            OAuth token
        """
        # After the user has authorized this app for use in their Slack team,
        # Slack returns a temporary authorization code that we'll exchange for
        # an OAuth token using the oauth.access endpoint
        auth_response = self.client.api_call(
                                "oauth.access",
                                client_id=self.oauth["client_id"],
                                client_secret=self.oauth["client_secret"],
                                code=code
                                )
        # To keep track of authorized teams and their associated OAuth tokens,
        # we will save the team ID and bot tokens to the global
        # authed_teams object
        team_id = auth_response["team_id"]
        authed_teams[team_id] = {"bot_token":
                                 auth_response["bot"]["bot_access_token"]}
        # Then we'll reconnect to the Slack Client with the correct team's
        # bot token
        self.client = slackclient.SlackClient(authed_teams[team_id]["bot_token"])

        # Retrieve and update slack bot id
        for user in self.client.api_call('users.list').get('members'):
            if user.get('name') == settings.BOT_NAME:
                self.logger.info(f"bot id is {user.get('id')}")
                self.botId = user.get('id')
