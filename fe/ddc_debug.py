import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_command_direct(command):
    """Run a command directly and show all output."""
    logger.info(f"\nTesting command: {' '.join(command)}")
    try:
        result = subprocess.run(command, 
                              capture_output=True, 
                              text=True)
        
        logger.info("Return code: %d", result.returncode)
        
        if result.stdout:
            logger.info("\nStandard output:")
            logger.info(result.stdout)
            
        if result.stderr:
            logger.info("\nStandard error:")
            logger.info(result.stderr)
            
        return result.returncode == 0
        
    except FileNotFoundError:
        logger.error("\nCommand not found. Is winddcutil in your PATH?")
        return False
    except Exception as e:
        logger.error("\nUnexpected error: %s", str(e))
        return False

def check_environment():
    """Check system environment variables."""
    logger.info("\nChecking system PATH:")
    path = os.environ.get('PATH', '')
    paths = path.split(';')
    for p in paths:
        if 'winddcutil' in p.lower():
            logger.info(f"Found winddcutil in PATH: {p}")
            break
    else:
        logger.info("winddcutil not found in PATH")

def main():
    logger.info("Starting DDC debug tests...")

    # Basic commands to test
    commands = [
        ["winddcutil", "--version"],
        ["winddcutil", "detect"],
        ["winddcutil", "list"],
        ["winddcutil", "capabilities"],
        ["winddcutil", "environment"]
    ]

    success = True
    for command in commands:
        if not test_command_direct(command):
            success = False
            logger.error(f"\nCommand failed: {' '.join(command)}")
        
    logger.info("\nSummary:")
    if success:
        logger.info("All commands completed successfully")
    else:
        logger.info("Some commands failed - check output above")

if __name__ == "__main__":
    import os
    check_environment()
    main()