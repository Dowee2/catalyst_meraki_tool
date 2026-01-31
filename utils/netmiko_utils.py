"""
Netmiko Baseline Utilities

Reusable functions for Netmiko network device automation.
Eliminates code duplication across automation scripts.

Environment Variables:
    NETMIKO_USERNAME_1, NETMIKO_PASSWORD_1  - Primary credentials
    NETMIKO_USERNAME_2, NETMIKO_PASSWORD_2  - Secondary credentials
    NETMIKO_USERNAME_N, NETMIKO_PASSWORD_N  - Additional credentials (N=3,4,5...)
    NETMIKO_ENABLE_SECRET                   - Enable mode secret
    NETMIKO_DEFAULT_TIMEOUT                 - Connection timeout (default: 60)
    NETMIKO_DEFAULT_READ_TIMEOUT            - Read timeout override (default: 120)

Usage Example:
    from netmiko_utils import connect_with_retry, save_config_to_folder, configure_logging

    logger = configure_logging('my_script.log')
    net_connect, cred = connect_with_retry('192.168.1.1', logger=logger)

    if net_connect:
        with net_connect:
            net_connect.enable()
            # ... do work ...
            save_config_to_folder(net_connect, './configs')
"""

import os
import logging
import getpass
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException


def load_credentials_from_env(include_user_prompt=True):
    """
    Load credentials from environment variables.

    Loads credentials in the format:
    - NETMIKO_USERNAME_1, NETMIKO_PASSWORD_1
    - NETMIKO_USERNAME_2, NETMIKO_PASSWORD_2
    - etc.

    Args:
        include_user_prompt (bool): If True, prepends interactive user prompt as first credential.
                                   Uses getpass.getuser() and getpass.getpass() for secure input.
                                   Default: True

    Returns:
        list: List of credential dictionaries [{'username': 'x', 'password': 'y'}, ...]
              Returns empty list if no credentials found.

    Example:
        >>> # With environment variables set
        >>> creds = load_credentials_from_env(include_user_prompt=False)
        >>> print(creds)
        [{'username': 'admin', 'password': '***'}, {'username': 'cisco', 'password': '***'}]
    """
    credentials = []

    # Add interactive user prompt as first credential
    if include_user_prompt:
        try:
            username = getpass.getuser()
            password = getpass.getpass("Password: ")
            credentials.append({'username': username, 'password': password})
        except Exception as e:
            logging.warning(f"Could not get user credentials interactively: {e}")

    # Load numbered credentials from environment
    index = 1
    while True:
        username = os.getenv(f'NETMIKO_USERNAME_{index}')
        password = os.getenv(f'NETMIKO_PASSWORD_{index}')

        if username and password:
            credentials.append({'username': username, 'password': password})
            index += 1
        else:
            break

    if not credentials:
        logging.warning("No credentials loaded. Set NETMIKO_USERNAME_N and NETMIKO_PASSWORD_N environment variables.")

    return credentials


def mask_credential(credential):
    """
    Mask password in credential dict for safe logging.

    Args:
        credential (dict): Credential dict with 'username' and 'password' keys

    Returns:
        str: Formatted string 'username/***' for safe logging

    Example:
        >>> mask_credential({'username': 'admin', 'password': 'secret123'})
        'admin/***'
    """
    return f"{credential.get('username', 'unknown')}/***"


def connect_with_retry(ip_address, credentials=None, device_type='cisco_ios',
                       enable_secret=None, timeout=None, read_timeout_override=None,
                       log_auth_failures=True, logger=None):
    """
    Connect to network device with automatic credential retry logic.

    Tries each credential in sequence until successful connection or all fail.
    Handles NetMikoTimeoutException, NetMikoAuthenticationException, and general exceptions.

    Args:
        ip_address (str): Device IP address or hostname
        credentials (list, optional): List of credential dicts [{'username': 'x', 'password': 'y'}, ...].
                                     If None, loads from environment using load_credentials_from_env().
        device_type (str): Netmiko device type. Default: 'cisco_ios'
        enable_secret (str, optional): Enable mode secret. If None, uses NETMIKO_ENABLE_SECRET env var.
        timeout (int, optional): Connection timeout in seconds. If None, uses NETMIKO_DEFAULT_TIMEOUT env var or 60.
        read_timeout_override (int, optional): Read timeout in seconds. If None, uses NETMIKO_DEFAULT_READ_TIMEOUT env var.
        log_auth_failures (bool): Whether to log authentication failures. Default: True
        logger (logging.Logger, optional): Logger instance. If None, uses module logger.

    Returns:
        tuple: (net_connect, successful_credential) if successful
               (None, None) if all credentials fail

    Raises:
        NetMikoTimeoutException: If connection times out (propagated to caller, not caught)

    Example:
        >>> net_connect, cred = connect_with_retry('192.168.1.1')
        >>> if net_connect:
        ...     with net_connect:
        ...         output = net_connect.send_command('show version')
        ...         print(output)
    """
    # Use module logger if none provided
    if logger is None:
        logger = logging.getLogger(__name__)

    # Load credentials from environment if not provided
    if credentials is None:
        credentials = load_credentials_from_env(include_user_prompt=True)

    if not credentials:
        logger.error(f"No credentials available to connect to {ip_address}")
        return None, None

    # Load defaults from environment
    if enable_secret is None:
        enable_secret = os.getenv('NETMIKO_ENABLE_SECRET', 'Southwire!')

    if timeout is None:
        timeout = int(os.getenv('NETMIKO_DEFAULT_TIMEOUT', '60'))

    if read_timeout_override is None:
        read_timeout_env = os.getenv('NETMIKO_DEFAULT_READ_TIMEOUT')
        if read_timeout_env:
            read_timeout_override = int(read_timeout_env)

    # Try each credential
    successful_authentication = False
    for credential in credentials:
        try:
            # Build device connection parameters
            device = {
                'device_type': device_type,
                'ip': ip_address,
                'username': credential['username'],
                'password': credential['password'],
                'secret': enable_secret,
                'timeout': timeout
            }

            # Add read_timeout_override if specified
            if read_timeout_override:
                device['read_timeout_override'] = read_timeout_override

            # Attempt connection
            net_connect = ConnectHandler(**device)
            successful_authentication = True

            logger.info(f"Successfully connected to {ip_address} using {mask_credential(credential)}")
            return net_connect, credential

        except NetMikoTimeoutException:
            logger.error(f"Connection timed out for {ip_address}")
            # Timeout means network issue, don't try other credentials
            return None, None

        except NetMikoAuthenticationException:
            if log_auth_failures:
                logger.warning(f"Authentication failed for {ip_address} using {mask_credential(credential)}")
            # Continue to next credential
            continue

        except Exception as error:
            logger.error(f"Failed to connect to {ip_address}: {error}")
            # Unexpected error, don't try other credentials
            return None, None

    # All credentials failed
    if not successful_authentication:
        logger.error(f"All credentials failed for {ip_address}")
        return None, None


def save_config_to_folder(net_connect, base_folder_path,
                          location_delimiter='-', location_index=0):
    """
    Save device running config to organized folder structure.

    Extracts location from hostname and creates folder structure:
    base_folder_path/LOCATION/HOSTNAME_config.txt

    Args:
        net_connect: Active Netmiko connection object
        base_folder_path (str): Base directory for configs (e.g., './configs')
        location_delimiter (str): Delimiter to split hostname. Default: '-'
                                  Use '_' for hostnames like SITE_DEVICE_01
        location_index (int): Index of location in split hostname. Default: 0
                              For 'CORP-MTN-SW-01' split by '-', index 0 = 'CORP'
                              For 'SITE_DEVICE_01' split by '_', index 0 = 'SITE'

    Returns:
        str: Full path to saved config file

    Example:
        >>> # Device hostname: CORP-MTN-SW-01
        >>> save_config_to_folder(net_connect, './configs')
        './configs/CORP/CORP-MTN-SW-01_config.txt'

        >>> # Device hostname: SITE_DEVICE_01
        >>> save_config_to_folder(net_connect, './configs', location_delimiter='_')
        './configs/SITE/SITE_DEVICE_01_config.txt'
    """
    # Get device hostname (remove trailing prompt character)
    device_name = net_connect.find_prompt()[:-1]

    # Extract location from hostname
    try:
        location = device_name.split(location_delimiter)[location_index]
    except IndexError:
        # If split fails, use full device name as location
        location = device_name
        logging.warning(f"Could not parse location from {device_name}, using full name as location")

    # Create folder structure
    folder_path = os.path.join(base_folder_path, location)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Define file path
    file_path = os.path.join(folder_path, f"{device_name}_config.txt")

    # Retrieve running config
    running_config = net_connect.send_command('show run')

    # Write config to file
    with open(file_path, 'w') as file:
        file.write(running_config)

    print(f"Configuration saved for {device_name} in {file_path}")
    logging.info(f"Configuration saved for {device_name} in {file_path}")

    return file_path


def configure_logging(log_filename='netmiko_automation.log',
                      log_level=logging.WARNING,
                      log_format='%(asctime)s %(levelname)s:%(message)s'):
    """
    Configure logging with standard format for Netmiko automation scripts.

    Sets up basic logging configuration with consistent format.

    Args:
        log_filename (str): Log file name. Default: 'netmiko_automation.log'
        log_level (int): Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL).
                        Default: logging.WARNING
        log_format (str): Log message format. Default: '%(asctime)s %(levelname)s:%(message)s'

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> logger = configure_logging('my_script.log', logging.INFO)
        >>> logger.info('Script started')
        >>> logger.warning('Authentication failed')
        >>> logger.error('Connection timeout')
    """
    logging.basicConfig(
        filename=log_filename,
        level=log_level,
        format=log_format
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: {log_filename} (level: {logging.getLevelName(log_level)})")

    return logger


def get_running_config(ip_address, credentials=None, command='show running-config',
                       use_textfsm=False, read_timeout=120, logger=None):
    """
    Universal switch connection and data retrieval function.

    Connects to a network switch and retrieves data using a specified command.
    Uses existing connect_with_retry() for credential management and connection.

    Args:
        ip_address (str): Switch IP address or hostname
        credentials (list, optional): List of credential dicts. If None, loads from environment.
        command (str): Command to execute on switch. Default: 'show running-config'
        use_textfsm (bool): Use TextFSM parsing for structured output. Default: False
        read_timeout (int): Read timeout for command execution. Default: 120 seconds
        logger (logging.Logger, optional): Logger instance. If None, uses module logger.

    Returns:
        tuple: (output, hostname) if successful
               (None, None) if connection or command fails

    Example:
        >>> # Get running config
        >>> config, hostname = get_running_config('192.168.1.1', command='show running-config')

        >>> # Get interface status with TextFSM parsing
        >>> interfaces, hostname = get_running_config('192.168.1.1',
        ...                                            command='show ip int brief',
        ...                                            use_textfsm=True)

        >>> # Get MAC address table
        >>> macs, hostname = get_running_config('192.168.1.1',
        ...                                     command='show mac address-table',
        ...                                     use_textfsm=True,
        ...                                     read_timeout=90)
    """
    # Use module logger if none provided
    if logger is None:
        logger = logging.getLogger(__name__)

    # Connect to switch with credential retry
    net_connect, successful_cred = connect_with_retry(
        ip_address,
        credentials=credentials,
        read_timeout_override=read_timeout,
        logger=logger
    )

    if not net_connect:
        logger.error(f"Failed to connect to switch at {ip_address}")
        return None, None

    try:
        with net_connect:
            # Enable privileged mode
            net_connect.enable()

            # Get hostname
            hostname = net_connect.find_prompt().strip('#')

            # Execute command
            output = net_connect.send_command(command, use_textfsm=use_textfsm, read_timeout=read_timeout)

            # Save config (if running-config command)
            if 'running-config' in command:
                net_connect.save_config()

            logger.info(f"Successfully retrieved data from {hostname} ({ip_address})")
            return output, hostname

    except Exception as error:
        logger.error(f"Error retrieving data from {ip_address}: {error}")
        return None, None


# Module-level logger for internal use
_module_logger = logging.getLogger(__name__)
