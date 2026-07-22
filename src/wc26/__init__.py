"""WC26 Transfer Intelligence analytics package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("wc26-transfer-intelligence")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
