#!/usr/bin/env python

import os
import sys


if __name__ == "__main__":
    # Add parent dir to PYTHONPATH to allow `tests_django` import
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests_django.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
