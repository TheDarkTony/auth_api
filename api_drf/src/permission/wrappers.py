from core_contracts.handler import DemandContext, Response, PipelineProtocol, Handler

from core.permission.permissions import Arguments
from core.permission.demands import PermissionDemand

class DemandHandlerWrapper:
    def __init__(self, pipeline: PipelineProtocol, handler: Handler) -> None:
        self._pipeline = pipeline
        self._handler = handler


class ListAppResourcesWrapper(DemandHandlerWrapper):

    def list_app_resource(self, ctx: DemandContext) -> Response:
        return self._pipeline.execute(ctx, self._handler)


class ListRolesWrapper(DemandHandlerWrapper):

    def list_roles(self, ctx: DemandContext) -> Response:
        return self._pipeline.execute(ctx, self._handler)


class ListPermissionsWrapper(DemandHandlerWrapper):

    def list_permissions(self, ctx: DemandContext, role_id, resource_id) -> Response:

        if role_id is not None:
            ctx.arguments[Arguments.ROLE_ID] = int(role_id)

        if resource_id is not None:
            ctx.arguments[Arguments.RESOURCE_ID] = int(resource_id)

        return self._pipeline.execute(ctx, self._handler)


class EditPermissionWrapper(DemandHandlerWrapper):

    def edit_permission(self, ctx: DemandContext, role_id, resource_id, permission_id, demand: PermissionDemand) -> Response:

        if role_id is not None:
            ctx.arguments[Arguments.ROLE_ID] = int(role_id)

        if resource_id is not None:
            ctx.arguments[Arguments.RESOURCE_ID] = int(resource_id)

        if permission_id is not None:
            ctx.arguments[Arguments.PERMISSION_ID] = int(permission_id)

        ctx.demand = demand

        return self._pipeline.execute(ctx, self._handler)


class CreatePermissionWrapper(DemandHandlerWrapper):

    def create_permission(self, ctx: DemandContext, role_id, resource_id, demand: PermissionDemand) -> Response:

        if role_id is not None:
            ctx.arguments[Arguments.ROLE_ID] = int(role_id)

        if resource_id is not None:
            ctx.arguments[Arguments.RESOURCE_ID] = int(resource_id)

        ctx.demand = demand

        return self._pipeline.execute(ctx, self._handler)


class DeletePermissionWrapper(DemandHandlerWrapper):

    def delete_permission(self, ctx:DemandContext, permission_id) -> Response:

        if permission_id is not None:
            ctx.arguments[Arguments.PERMISSION_ID] = int(permission_id)

        return self._pipeline.execute(ctx, self._handler)


class FetchPermissionWrapper(DemandHandlerWrapper):

    def fetch_permission(self, ctx: DemandContext, permission_id) -> Response:

        if permission_id is not None:
            ctx.arguments[Arguments.PERMISSION_ID] = int(permission_id)

        return self._pipeline.execute(ctx, self._handler)