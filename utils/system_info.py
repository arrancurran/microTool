import platform
import subprocess

def get_computer_name():
    """Get the computer name of the system.
    
    Returns:
        str: The computer name of the system
        
    Note:
        This function works on all major operating systems (Windows, macOS, Linux).
        On Windows, it will return the computer name as shown in System Properties.
    """
    try:
        # Try platform.node() first as it's the most reliable cross-platform method
        name = platform.node()
        if name:
            return name
            
        # If platform.node() returns empty, try Windows-specific command
        if platform.system() == 'Windows':
            try:
                # This command works on Windows and returns the computer name
                result = subprocess.run(['hostname'], capture_output=True, text=True)
                if result.stdout:
                    return result.stdout.strip()
            except subprocess.SubprocessError:
                pass
                
        return "Unknown Computer"
        
    except Exception:
        return "Unknown Computer" 