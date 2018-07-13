import yaml

class Message(object):
    """
    Instantiates a Message object to create and manage
    Slack messages.
    """
    def __init__(self):
        super(Message, self).__init__()
        self.channel = ''
        self.timestamp = ''
        self.text = ''
        self.attachments = []