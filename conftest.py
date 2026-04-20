"""Pytest root marker.

Its presence makes pytest add this directory to ``sys.path`` during test
collection, so tests can ``from app.xxx import ...`` without needing the
package to be pip-installed.
"""
