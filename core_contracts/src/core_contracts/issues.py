

#Bad Request
class ValidationIssue(Exception): ...


class NotFoundEntryIssue(Exception): ...


class ForbiddenIssue(Exception): ...


class ApplicationIssue(Exception): ...


#500: please try latter, we are working on it
class ConfigurationIssue(Exception): ...


class ResourceDisposedIssue(Exception): ...