from polyrouter import LLMOrchestrator

gw = LLMGateway(
    groq={...},
    debug=True,        # major logs
    verbose=False      # in-depth trace
)