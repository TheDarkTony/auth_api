from contextlib import contextmanager

from dependency_injector import containers , providers
import valkey

from core.auth import signup
from core.auth import signin
from src.auth import wrappers as auth_wrappers

from core.identity import identities
from core.identity import profile
from core.identity import users
from src.identity import wrappers as identity_wrappers

from core.permission import permissions
from src.permission import wrappers as perm_wrappers

from repo_sqlalchemy import schema
from repo_sqlalchemy.identity import repo as ir
from repo_sqlalchemy.permission import repo as pr
from repo_sqlalchemy.temp_token import repo as tr

from queue_publishers import emailer_2fa

from core.pizza import orders
from src.pizza import wrappers as pizza_wrappers

from src.api_core.utils import UserTempBlackListValkey, AccessTokenBlackListValkey


@contextmanager
def db_seance_manager(engine: schema.Engine):
    m = schema.SeanceManager(engine, True)
    yield m
    m.dispose()

class AppContainer(containers.DeclarativeContainer):

    config = providers.Configuration()


    #core_dependencies
    ####db deps
    db_engine = providers.ThreadSafeSingleton(
        schema.create_engine
        , config.db.connection
        , pool_pre_ping=True
    )

    db_seance_manager = providers.ContextLocalResource(
        db_seance_manager
        , db_engine
    )

    identities_repo = providers.Factory(
        ir.IdentityRepository
        , db_seance_manager
    )

    users_repo = providers.Factory(
        ir.UserRepository
        , db_seance_manager
    )

    permissions_repo = providers.Factory(
        pr.RolePermissionRepository
        , db_seance_manager
    )

    roles_repo = providers.Factory(
        pr.RoleRepository
        , db_seance_manager
    )

    app_resources_repo = providers.Factory(
        pr.ApplicationResourceRepository
        , db_seance_manager
    )

    temp_tokens_repo = providers.Factory(
        tr.TempTokenRepository
        , db_seance_manager
    )

    valkey_client = providers.ThreadSafeSingleton(
        valkey.from_url,
        url=config.valkey.url
    )

    user_temp_black_list_repo = providers.Factory(
        UserTempBlackListValkey,
        valkey_client
    )
    access_token_black_list_repo = providers.Factory(
        AccessTokenBlackListValkey,
        valkey_client
    )

    ####queue deps

    queue_manager = providers.ThreadLocalSingleton(
        emailer_2fa.QueueManager
        , config.rabbitmq.host
        , config.rabbitmq.username
        , config.rabbitmq.password
        , 2
    )

    emailer_queue_client = providers.Factory(
        emailer_2fa.Emailer2FAPublisher
        , publisher=queue_manager
        , exchange_name=config.rabbitmq.exchanges.auth_2fa_emailer
    )

    #ListIdentities
    list_identities_pipeline = providers.Factory(
        identities.pipeline_list_identities
        , permissions_repo
    )
    list_identities_handler = providers.Factory(
        identities.ListIdentitiesHandler,
        identities_repo
    )
    list_identities_wrappers = providers.Factory(
        identity_wrappers.ListIdentitiesWrapper
        , pipeline = list_identities_pipeline
        , handler = list_identities_handler
    )

    #FetchIdentity
    fetch_identity_pipeline = providers.Factory(
        identities.pipeline_fetch_identity
        , permissions_repo
    )
    fetch_identity_handler = providers.Factory(
        identities.FetchIdentityHandler
        , identities_repo
    )
    fetch_identity_wrappers = providers.Factory(
        identity_wrappers.FetchIdentityWrapper
        , pipeline = fetch_identity_pipeline
        , handler = fetch_identity_handler
    )

    #EditIdentityDemographics
    edit_demographics_pipeline = providers.Factory(
        identities.pipeline_edit_demographics
        , permissions_repo
    )
    edit_demographics_handler = providers.Factory(
        identities.EditDemographicsHandler
        , identities_repo
    )
    edit_demographics_wrapper = providers.Factory(
        identity_wrappers.EditIdentityDemographicsWrapper
        , pipeline = edit_demographics_pipeline
        , handler = edit_demographics_handler
    )

    #FetchProfile
    fetch_profile_pipeline = providers.Factory(
        profile.pipeline_fetch_profile
        , permissions_repo
    )
    fetch_profile_handler = providers.Factory(
        profile.FetchProfileHandler
        , users_repo
        , identities_repo
    )
    fetch_profile_wrapper = providers.Factory(
        identity_wrappers.FetchProfileWrapper
        , pipeline = fetch_profile_pipeline
        , handler = fetch_profile_handler
    )

    #ListUsers
    list_users_pipeline = providers.Factory(
        users.pipeline_list_user
        , permissions_repo
    )
    list_users_handler = providers.Factory(
        users.ListUsersHandler
        , users_repo
    )
    list_users_wrapper = providers.Factory(
        identity_wrappers.ListUsersWrapper
        , pipeline = list_users_pipeline
        , handler = list_users_handler
    )

    #FetchUserDetails
    fetch_user_pipeline = providers.Factory(
        users.pipeline_fetch_user
        , permissions_repo
    )
    fetch_user_handler = providers.Factory(
        users.FetchUserHandler
        , users_repo
    )
    fetch_user_wrapper = providers.Factory(
        identity_wrappers.FetchUserWrapper
        , pipeline = fetch_user_pipeline
        , handler = fetch_user_handler
    )

    #DeleteUser
    delete_user_pipeline = providers.Factory(
        users.pipeline_delete_user
        , permissions_repo
    )
    delete_user_handler = providers.Factory(
        users.DeleteUserHandler
        , usr_repo=users_repo
        , user_temp_black_list_repo=user_temp_black_list_repo
        , access_token_seconds_ttl=config.auth.access_token_seconds_ttl
    )
    delete_user_wrapper = providers.Factory(
        identity_wrappers.DeleteUserWrapper
        , pipeline = delete_user_pipeline
        , handler = delete_user_handler
    )

    #EditUser
    edit_user_pipeline = providers.Factory(
        users.pipeline_edit_user
        , permissions_repo
    )
    edit_user_handler = providers.Factory(
        users.EditUserHandler
        , users_repo
    )
    edit_user_wrapper = providers.Factory(
        identity_wrappers.EditUserWrapper
        , pipeline = edit_user_pipeline
        , handler = edit_user_handler
    )

    #ChangeUserPwd
    change_user_pwd_pipeline = providers.Factory(
        users.pipeline_change_pwd
        , permissions_repo
    )
    chage_user_pwd_handler = providers.Factory(
        users.ChangePwdHandler
        , users_repo
    )
    change_user_pwd = providers.Factory(
        identity_wrappers.ChangePwdWrapper
        , pipeline = change_user_pwd_pipeline
        , handler = chage_user_pwd_handler
    )

    #SignUpWrapper
    auth_settings = providers.Singleton(
        signup.Settings,
        config.auth.default_role_id,
        config.auth.default_email_2fa_enabled,
        config.auth.email_code_seconds_ttl,
        config.auth.email_regex_template,
    )
    auth_util = providers.Factory(
        signup.AuthTokenUtil
        , secret_jwt_key=config.auth.secret_jwt_key
        , jwt_algorithm=config.auth.jwt_algorithm
        , access_token_seconds_ttl=config.auth.access_token_seconds_ttl
        , refresh_token_seconds_ttl=config.auth.refresh_token_seconds_ttl
    )

    sign_up_pipeline = providers.Factory(
        signup.pipeline_signup,
        auth_settings
    )
    sign_up_handler = providers.Factory(
        signup.SignUpHandler
        , identities_repo
        , users_repo
        , emailer_queue_client
        , auth_settings
    )
    sign_up_wrapper = providers.Factory(
        auth_wrappers.SignUpWrapper
        , pipeline = sign_up_pipeline
        , handler = sign_up_handler
    )

    #SignUp2FA
    signup_2fa_pipeline = providers.Factory(
        signup.pipeline_signup_2fa
    )
    signup_2fa_handler = providers.Factory(
        signup.SignUp2FAVerificationHandler
        , temp_tokens_repo
        , identities_repo
        , users_repo
        , auth_settings
        , auth_util
    )
    signup_2fa_wrapper = providers.Factory(
        auth_wrappers.SignUp2FAWrapper
        , pipeline = signup_2fa_pipeline
        , handler = signup_2fa_handler
    )

    #SignInWrapper
    sign_in_pipeline = providers.Factory(
        signin.pipeline_sign_in,
        auth_settings
    )
    sign_in_handler = providers.Factory(
        signin.SingInHandler
        , users_repo
        , emailer_queue_client
        , auth_settings
        , auth_util
    )
    sign_in_wrapper = providers.Factory(
        auth_wrappers.SignInWrapper
        , pipeline = sign_in_pipeline
        , handler = sign_in_handler
    )

    #SignIn2FAWrapper
    signin_2fa_pipeline = providers.Factory(
        signin.pipeline_sign_in_2fa_feedback
    )
    signin_2fa_handler = providers.Factory(
        signin.SignIn2FAHandler
        , users_repo
        , temp_tokens_repo
        , auth_util
    )
    signin_2fa_wrapper = providers.Factory(
        auth_wrappers.SignIn2FAWrapper
        , pipeline = signin_2fa_pipeline
        , handler = signin_2fa_handler
    )



    #ListAppResourcesWrapper
    list_app_res_pipeline = providers.Factory(
        permissions.list_app_resources_pipeline,
        permissions_repo
    )

    list_app_res_handler = providers.Factory(
        permissions.ListAppResourcesHandler,
        app_resources_repo
    )

    list_app_resources_wrapper = providers.Factory(
        perm_wrappers.ListAppResourcesWrapper
        , pipeline = list_app_res_pipeline
        , handler = list_app_res_handler
    )

    #ListRolesWrapper
    list_roles_pipeline = providers.Factory(
        permissions.list_roles_pipeline,
        permissions_repo
    )
    list_roles_handler = providers.Factory(
        permissions.ListRolesHandler,
        roles_repo
    )
    list_roles_wrapper = providers.Factory(
        perm_wrappers.ListRolesWrapper
        , pipeline = list_roles_pipeline
        , handler = list_roles_handler
    )

    #ListPermissionsWrapper
    list_permissions_pipeline = providers.Factory(
        permissions.list_permissions_pipeline,
        permissions_repo
    )
    list_permissions_handler = providers.Factory(
        permissions.ListPermissionsHandler,
        permissions_repo
    )
    list_permissions_wrapper = providers.Factory(
        perm_wrappers.ListPermissionsWrapper
        , pipeline = list_permissions_pipeline
        , handler = list_permissions_handler
    )


    #EditPermissionWrapper
    edit_permission_pipeline = providers.Factory(
        permissions.edit_permission_pipeline,
        permissions_repo
    )
    edit_permission_handler = providers.Factory(
        permissions.EditPermissionHandler,
        permissions_repo
    )

    edit_permission_wrapper = providers.Factory(
        perm_wrappers.EditPermissionWrapper
        , pipeline = edit_permission_pipeline
        , handler = edit_permission_handler
    )

    #CreatePermissionWrapper
    create_permission_pipeline = providers.Factory(
        permissions.create_permission_pipeline,
        permissions_repo
    )
    create_permission_handler = providers.Factory(
        permissions.CreatePermissionHandler,
        permissions_repo
    )
    create_permission_wrapper = providers.Factory(
        perm_wrappers.CreatePermissionWrapper
        , pipeline = create_permission_pipeline
        , handler = create_permission_handler
    )

    #DeletePermissionWrapper
    delete_permission_pipeline = providers.Factory(
        permissions.delete_permission_pipeline,
        permissions_repo
    )
    delete_permission_handler = providers.Factory(
        permissions.DeletePermissionHandler,
        permissions_repo
    )
    delete_permission_wrapper = providers.Factory(
        perm_wrappers.DeletePermissionWrapper
        , pipeline = delete_permission_pipeline
        , handler = delete_permission_handler
    )

    #FetchPermissionWrapper
    fetch_permission_pipeline = providers.Factory(
        permissions.fetch_permission_pipeline,
        permissions_repo
    )
    fetch_permission_handler = providers.Factory(
        permissions.FetchPermissionHandler,
        permissions_repo
    )
    fetch_permission_wrapper = providers.Factory(
        perm_wrappers.FetchPermissionWrapper
        , pipeline = fetch_permission_pipeline
        , handler = fetch_permission_handler
    )

    #pizza deps
    read_order_pipeline = providers.Factory(
        orders.read_order_pipeline,
        permissions_repo
    )
    create_order_pipeline = providers.Factory(
        orders.create_order_pipeline,
        permissions_repo
    )
    edit_order_pipeline = providers.Factory(
        orders.edit_order_pipeline,
        permissions_repo
    )
    delete_order_pipeline = providers.Factory(
        orders.delete_order_pipeline,
        permissions_repo
    )
    list_order_pipeline = providers.Factory(
        orders.list_order_pipeline,
        permissions_repo
    )

    read_order_handler = providers.Factory(
        orders.ReadOrderHandler
    )
    create_order_handler = providers.Factory(
        orders.CreateOrderHandler
    )
    edit_order_handler = providers.Factory(
        orders.EditOrderHandler
    )
    delete_order_handler = providers.Factory(
        orders.DeleteOrderHandler
    )
    list_order_handler = providers.Factory(
        orders.ListOrdersHandler
    )


    create_order_wrapper = providers.Factory(
        pizza_wrappers.CreateOrderWrapper,
        create_order_pipeline,
        create_order_handler
    )
    read_order_wrapper = providers.Factory(
        pizza_wrappers.ReadOrdersWrapper,
        read_order_pipeline,
        read_order_handler
    )
    edit_order_wrapper = providers.Factory(
        pizza_wrappers.EditOrdersWrapper,
        edit_order_pipeline,
        edit_order_handler
    )
    delete_order_wrapper = providers.Factory(
        pizza_wrappers.DeleteOrdersWrapper,
        delete_order_pipeline,
        delete_order_handler
    )
    list_orders_wrapper = providers.Factory(
        pizza_wrappers.ListOrdersWrapper,
        list_order_pipeline,
        list_order_handler
    )