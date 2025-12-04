"""
Configuration helper functions for reading/writing settings.ini
"""
import configparser
import os


def get_config_path() -> str:
    """Get path to settings.ini"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.ini')


def get_ai_consent() -> bool:
    """Get AI consent status from settings.ini

    Returns:
        True if consent given, False otherwise
    """
    config = configparser.ConfigParser()
    config_path = get_config_path()

    try:
        config.read(config_path, encoding='utf-8')

        if config.has_section('ai') and config.has_option('ai', 'consent_given'):
            return config.getboolean('ai', 'consent_given')
        else:
            # Default to False if not set
            return False
    except Exception as e:
        print(f"[WARN] Failed to read AI consent: {e}")
        return False


def set_ai_consent(value: bool):
    """Set AI consent status in settings.ini

    Args:
        value: True to give consent, False to revoke
    """
    config = configparser.ConfigParser()
    config_path = get_config_path()

    try:
        # Read existing config
        config.read(config_path, encoding='utf-8')

        # Ensure [ai] section exists
        if not config.has_section('ai'):
            config.add_section('ai')

        # Set value
        config.set('ai', 'consent_given', str(value).lower())

        # Write back to file
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)

        print(f"[INFO] AI consent set to: {value}")
    except Exception as e:
        print(f"[ERROR] Failed to set AI consent: {e}")


def get_config_value(section: str, option: str, fallback=None):
    """Get any config value from settings.ini

    Args:
        section: Config section name
        option: Config option name
        fallback: Default value if not found

    Returns:
        Config value or fallback
    """
    config = configparser.ConfigParser()
    config_path = get_config_path()

    try:
        config.read(config_path, encoding='utf-8')

        if config.has_section(section) and config.has_option(section, option):
            return config.get(section, option)
        else:
            return fallback
    except Exception as e:
        print(f"[WARN] Failed to read config value [{section}].{option}: {e}")
        return fallback


def set_config_value(section: str, option: str, value: str):
    """Set any config value in settings.ini

    Args:
        section: Config section name
        option: Config option name
        value: Value to set (will be converted to string)
    """
    config = configparser.ConfigParser()
    config_path = get_config_path()

    try:
        # Read existing config
        config.read(config_path, encoding='utf-8')

        # Ensure section exists
        if not config.has_section(section):
            config.add_section(section)

        # Set value
        config.set(section, option, str(value))

        # Write back to file
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)

        print(f"[INFO] Config set: [{section}].{option} = {value}")
    except Exception as e:
        print(f"[ERROR] Failed to set config value: {e}")
