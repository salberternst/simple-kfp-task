import base64
import zlib
import inspect
import inspect
import os


def encode_string_to_base64(input_string: str):
    """
    Encodes a string to base64 format.

    Args:
        input_string (str): The string to be encoded.

    Returns:
        str: The base64 encoded string.
    """
    if not input_string.endswith('\n'):
        input_string += '\n'
    input_bytes = zlib.compress(
        input_string.encode('utf-8'), level=9, wbits=16 + 15)
    base64_bytes = base64.b64encode(input_bytes)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


def get_caller_filename():
    """
    Returns the filename of the caller function.

    Returns:
        str: The filename of the caller function.
    """
    return inspect.stack()[-1].filename


def get_relative_path(base_path: str, target_path: str) -> str:
    """
    Returns the relative path from the base path to the target path.

    Args:
        base_path (str): The base path.
        target_path (str): The target path.

    Returns:
        str: The relative path from the base path to the target path.
    """
    return os.path.relpath(target_path, base_path)