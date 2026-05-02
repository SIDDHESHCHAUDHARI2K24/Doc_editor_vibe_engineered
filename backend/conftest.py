"""Pytest configuration for backend tests."""
import os


def pytest_configure(config):
    os.environ["ENVIRONMENT"] = "test"
