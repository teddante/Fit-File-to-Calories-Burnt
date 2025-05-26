"""
Main entry point for the Fit-File-to-Calories-Burnt application.

This module serves as the minimal entry point that delegates to the CLI menu system.
All business logic has been extracted to appropriate modules for better separation of concerns.
"""

from src.cli.menu import run_application

if __name__ == '__main__':
    run_application()
