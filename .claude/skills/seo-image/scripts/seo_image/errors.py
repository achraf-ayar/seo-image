class FatalError(Exception):
    """Stops the whole run (exit code 2): bad domain, unsafe output folder, no inputs."""


class ImageError(Exception):
    """Fails one image; carries a reason for the report."""
