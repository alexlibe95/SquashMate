#!/usr/bin/env python3
"""
SquashMate Launcher Wrapper
This script wraps AppImage launches to provide logging when apps are started from desktop entries.
"""

import sys
import os
import subprocess
import datetime
from pathlib import Path


def setup_logging():
    """Setup logging directory and return paths."""
    log_dir = Path.home() / ".local" / "share" / "squashmate"
    apps_log_dir = log_dir / "apps"
    
    # Create directories if they don't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    apps_log_dir.mkdir(exist_ok=True)
    
    return log_dir, apps_log_dir


def log_launch_attempt(app_name, command, success=True, error_output=None, log_dir=None):
    """Log application launch attempts."""
    if not log_dir:
        _, apps_log_dir = setup_logging()
    else:
        apps_log_dir = log_dir / "apps"
    
    app_log_file = apps_log_dir / f"{app_name}.log"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open(app_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Desktop Launch: {timestamp}\n")
            f.write(f"Command: {' '.join(command)}\n")
            f.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")
            f.write(f"Launched from: Desktop Entry\n")
            
            if not success and error_output:
                f.write(f"\nError Output:\n{error_output}\n")
            elif success:
                f.write(f"\nApplication started successfully from desktop.\n")
            
            f.write(f"{'='*60}\n")
    except Exception as e:
        # If logging fails, write to a fallback location
        fallback_log = Path.home() / "squashmate_launch_errors.log"
        with open(fallback_log, 'a') as f:
            f.write(f"{timestamp}: Failed to log for {app_name}: {str(e)}\n")


def main():
    """Main launcher function."""
    if len(sys.argv) < 3:
        print("Usage: squashmate_launcher.py <app_name> <apprun_path> [additional_args...]")
        sys.exit(1)
    
    app_name = sys.argv[1]
    apprun_path = sys.argv[2]
    additional_args = sys.argv[3:] if len(sys.argv) > 3 else []
    
    # Setup logging
    log_dir, _ = setup_logging()
    
    # Get the directory containing AppRun - critical for APPDIR resolution
    apprun_dir = os.path.dirname(os.path.abspath(apprun_path))
    
    # Prepare command - try with --no-sandbox first, fallback without it
    command_with_sandbox = [apprun_path, '--no-sandbox'] + additional_args
    command_without_sandbox = [apprun_path] + additional_args
    
    try:
        # Check if AppRun exists and is executable
        if not os.path.exists(apprun_path):
            error_msg = f"AppRun file not found: {apprun_path}"
            log_launch_attempt(app_name, command_with_sandbox, success=False, error_output=error_msg, log_dir=log_dir)
            print(f"Error: {error_msg}")
            sys.exit(1)
        
        if not os.access(apprun_path, os.X_OK):
            error_msg = f"AppRun file is not executable: {apprun_path}"
            log_launch_attempt(app_name, command_with_sandbox, success=False, error_output=error_msg, log_dir=log_dir)
            print(f"Error: {error_msg}")
            sys.exit(1)
        
        # Try launching with --no-sandbox first
        success = False
        final_command = command_with_sandbox
        
        try:
            process = subprocess.Popen(
                command_with_sandbox,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=apprun_dir
            )
            
            # Give the process a moment to start and potentially fail immediately
            try:
                stdout, stderr = process.communicate(timeout=3)
                
                if process.returncode != 0:
                    # Check if the error is about unknown --no-sandbox option
                    error_output = stderr or stdout or ""
                    if "no-sandbox" in error_output.lower() and "unknown" in error_output.lower():
                        # Try without --no-sandbox
                        print("Retrying without --no-sandbox flag...")
                        final_command = command_without_sandbox
                        
                        process = subprocess.Popen(
                            command_without_sandbox,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=apprun_dir
                        )
                        
                        try:
                            stdout, stderr = process.communicate(timeout=3)
                            if process.returncode != 0:
                                error_output = stderr or stdout or f"Process exited with code {process.returncode}"
                                log_launch_attempt(app_name, final_command, success=False, error_output=error_output, log_dir=log_dir)
                                print(f"Application failed to start: {error_output}")
                                sys.exit(process.returncode)
                            else:
                                # Success without --no-sandbox
                                log_launch_attempt(app_name, final_command, success=True, log_dir=log_dir)
                                success = True
                                
                        except subprocess.TimeoutExpired:
                            # Process is still running - success
                            # Don't kill it! Just log success and let it continue running
                            log_launch_attempt(app_name, final_command, success=True, log_dir=log_dir)
                            success = True
                    else:
                        # Different error, not related to --no-sandbox
                        log_launch_attempt(app_name, final_command, success=False, error_output=error_output, log_dir=log_dir)
                        print(f"Application failed to start: {error_output}")
                        sys.exit(process.returncode)
                else:
                    # Process completed successfully with --no-sandbox
                    log_launch_attempt(app_name, final_command, success=True, log_dir=log_dir)
                    success = True
                    
            except subprocess.TimeoutExpired:
                # Process is still running after timeout - this is good for GUI apps
                # Don't kill it! Just log success and let it continue running
                log_launch_attempt(app_name, final_command, success=True, log_dir=log_dir)
                success = True
                
        except Exception as launch_error:
            # If launching with --no-sandbox failed completely, try without it
            if final_command == command_with_sandbox:
                try:
                    final_command = command_without_sandbox
                    process = subprocess.Popen(
                        command_without_sandbox,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=apprun_dir
                    )
                    
                    try:
                        stdout, stderr = process.communicate(timeout=3)
                        if process.returncode != 0:
                            error_output = stderr or stdout or f"Process exited with code {process.returncode}"
                            log_launch_attempt(app_name, final_command, success=False, error_output=error_output, log_dir=log_dir)
                            print(f"Application failed to start: {error_output}")
                            sys.exit(process.returncode)
                        else:
                            log_launch_attempt(app_name, final_command, success=True, log_dir=log_dir)
                            success = True
                            
                    except subprocess.TimeoutExpired:
                        # Process is still running - success
                        # Don't kill it! Just log success and let it continue running
                        log_launch_attempt(app_name, final_command, success=True, log_dir=log_dir)
                        success = True
                        
                except Exception as fallback_error:
                    error_msg = f"Failed to launch with and without --no-sandbox: {str(fallback_error)}"
                    log_launch_attempt(app_name, final_command, success=False, error_output=error_msg, log_dir=log_dir)
                    print(f"Error: {error_msg}")
                    sys.exit(1)
            else:
                raise launch_error
    
    except FileNotFoundError:
        error_msg = f"Command not found: {apprun_path}"
        log_launch_attempt(app_name, command_with_sandbox, success=False, error_output=error_msg, log_dir=log_dir)
        print(f"Error: {error_msg}")
        sys.exit(1)
        
    except PermissionError:
        error_msg = f"Permission denied: {apprun_path}"
        log_launch_attempt(app_name, command_with_sandbox, success=False, error_output=error_msg, log_dir=log_dir)
        print(f"Error: {error_msg}")
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_launch_attempt(app_name, command_with_sandbox, success=False, error_output=error_msg, log_dir=log_dir)
        print(f"Error: {error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()