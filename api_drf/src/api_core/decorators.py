
def allow_anonymous():
    def decorator(api_view):
        api_view.allow_anonymous = True
        return api_view

    return decorator


def attach_serializer(serializer):
    def decorator(api_view):
        api_view.cls.serializer_class = serializer
        api_view.view_class.serializer_class = serializer
        return api_view

    return decorator
