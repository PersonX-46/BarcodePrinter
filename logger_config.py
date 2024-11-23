import logging
import os
from logging.handlers import RotatingFileHandler
import json

def setup_logger(window_name, log_file='C:/barcode/barcode_app.log'):

    config_path = r"C:\barcode\barcode.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            if config['logging']:
                log_dir = os.path.dirname(log_file)  # Extract the directory from the full path
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)  # Create the directory if it doesn't exist

                # Create a logger for the specific window
                logger = logging.getLogger(window_name)
                logger.setLevel(logging.DEBUG)  # Set the minimum log level

                # Create handlers
                file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)  # 5MB per file
                file_handler.setLevel(logging.DEBUG)

                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)

                # Set a formatter for the handlers
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)

                # Add handlers to the logger
                if not logger.handlers:  # Prevent duplicate handlers
                    logger.addHandler(file_handler)
                    logger.addHandler(console_handler)

                return logger
            
    except FileNotFoundError:
        print(f'Configuration file not found at {config_path}')
        exit(1)
    except json.JSONDecodeError:
        print('Error parsing the configuration file.')
        exit(1)
    except KeyError as e:
        print(f'Missing key in configuration file: {e}')
        exit(1)

