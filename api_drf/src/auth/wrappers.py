from core_contracts.handler import DemandContext, Response, PipelineProtocol, Handler

from core.identity.demands import SignUpDemand, SignInDemand, Sign2FAFeedbackDemand


class DemandHandlerWrapper:
    def __init__(self, pipeline: PipelineProtocol, handler: Handler) -> None:
        self._pipeline = pipeline
        self._handler = handler


class SignUpWrapper(DemandHandlerWrapper):

    def sign_up(self, ctx: DemandContext, demand: SignUpDemand) -> Response:
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)


class SignUp2FAWrapper(DemandHandlerWrapper):

    def verify_2fa_signup(self, ctx: DemandContext, demand:Sign2FAFeedbackDemand) -> Response:
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)


class SignInWrapper(DemandHandlerWrapper):

    def sign_in(self, ctx: DemandContext, demand: SignInDemand) -> Response:
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)
     

class SignIn2FAWrapper(DemandHandlerWrapper):

    def verify_2fa_signin(self, ctx: DemandContext, demand: Sign2FAFeedbackDemand) -> Response:
        ctx.demand = demand
        return self._pipeline.execute(ctx, self._handler)
