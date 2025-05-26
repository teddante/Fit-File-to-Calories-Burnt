"""
Main menu module for the Fit-File-to-Calories-Burnt application.

This module contains the main menu function that provides the primary
user interface for selecting different calculator options.
"""

import logging
from src.core.logger import get_logger, initialize_logging
from .interface import (
    process_fit_files_option,
    calculate_karvonen_zones_option,
    cleanup_fit_files_option
)

# Get logger for this module
logger = get_logger(__name__)


def main():
    """
    Main function to provide calculator options to the user.
    
    This function displays the main menu and handles user input to navigate
    between different calculator options including FIT file processing,
    Karvonen heart rate zone calculation, and file cleanup.
    """
    try:
        while True:
            print("\nSelect a calculator option:")
            print("1. Calculate Calories from FIT file")
            print("2. Calculate Karvonen Heart Rate Zones")
            print("3. Clean up FIT file names")
            print("4. Exit")

            choice = input("Enter your choice (1, 2, 3, or 4): ").strip()

            if choice == '1':
                process_fit_files_option()
            elif choice == '2':
                calculate_karvonen_zones_option()
            elif choice == '3':
                cleanup_fit_files_option()
            elif choice == '4':
                print("Exiting program.")
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Critical error: {e}")


def run_application():
    """
    Entry point function that initializes logging and runs the main application.
    
    This function sets up the logging configuration and handles top-level
    exceptions that might occur during application startup or execution.
    """
    # Set logging level to INFO by default
    # Initialize logging
    initialize_logging(logging.INFO)
    # To enable debug logging, uncomment the following line:
    # logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Critical error: {e}")