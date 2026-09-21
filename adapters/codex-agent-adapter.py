

class CodexAgentAdapter:
    def __init__(self, agent):
        self.agent = agent

    def process_request(self, request):
        # Process the request using the agent
        response = self.agent.handle_request(request)
        return response