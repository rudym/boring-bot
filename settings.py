import os

DEBUG = True
ERRORS_TO = None
API_TOKEN = 'token'
CLIENT_ID = 'cid'
CLIENT_SECRET = 'secret'
VERIFICATION_TOKEN = 'vertok'
SCOPE = 'bot'

'''Hardcoded slack channel ID - to target specific channel'''
SLACK_CHANNEL_ID = 'channelid'

'''The amount of seconds before reprocessing events from slack'''
SOCKET_DELAY = 1

'''
Setup a comma delimited list of aliases that the bot will respond to.
Example: if you set ALIASES='!,$' then a bot which would respond to:
'botname hello'
will now also respond to
'$ hello'
'''
ALIASES = 'youralias'

'''
If you use Slack Web API to send messages (with
send_webapi(text, as_user=False) or reply_webapi(text, as_user=False)),
you can customize the bot logo by providing Icon or Emoji. If you use Slack
RTM API to send messages (with send() or reply()), or if as_user is True
(default), the used icon comes from bot settings and Icon or Emoji has no
effect.
'''
BOT_NAME = 'boring-bot'
BOT_ICON = 'urlicon'
BOT_EMOJI = ':nail_care:'

# for key in os.environ:
#     if key[:9] == 'SLACKBOT_':
#         name = key[9:]
#         globals()[name] = os.environ[key]