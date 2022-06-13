"""Project testing tools"""
import os


def get_resource_filename(local_filename):
    """Helper to get absolute file path from this test module."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resources", local_filename
    )
