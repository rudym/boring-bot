from state import State

# Start of our states
class NoState(State):

    def on_event(self, event):
        if event == 'dev_launched_release':
            return ReleaseInitiatedState()

        return self


class ReleaseInitiatedState(State):

    def on_event(self, event):
        if event == 'qa_accepted':
            return QaAcceptedState()
        if event == 'qa_denied':
            return QaDeniedState()

        return self


class QaAcceptedState(State):

    def on_event(self, event):
        if event == 'cc_accepted':
            return CcAcceptedState()

        return self


class QaDeniedState(State):

    def on_event(self, event):
        return self
        

class CcAcceptedState(State):

    def on_event(self, event):
        if event == 'devops_deployed':
            return ReleaseDeployedState()

        return self

class ReleaseDeployedState(State):

    def on_event(self, event):
        return self

# End of our states.