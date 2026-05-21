class DebupError(Exception):
    """Base class for user-facing Spork errors."""


class ConfigError(DebupError):
    pass


class BucketError(DebupError):
    pass


class IndexError(DebupError):
    pass


class AppNotFoundError(DebupError):
    pass


class DownloadError(DebupError):
    pass


class AptError(DebupError):
    pass


class DpkgError(DebupError):
    pass
