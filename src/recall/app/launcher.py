#!/usr/bin/env python3
"""Recall App Launcher.

This is the main entry point for the Recall.app bundle.
It handles first-run setup and launches the menu bar application.
"""

import sys
from pathlib import Path


def main():
    """Main entry point for Recall app."""
    # Ensure we can import recall modules
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from recall.app.installer import AppLauncher, LaunchMode

    # Check launch mode
    launcher = AppLauncher()
    mode = launcher.get_launch_mode()

    if mode == LaunchMode.FIRST_RUN_WIZARD:
        run_first_run_wizard(launcher)
    elif mode == LaunchMode.MODEL_DOWNLOAD:
        run_model_download()

    # Start the menu bar app
    run_menu_bar_app()


def run_first_run_wizard(launcher):
    """Run the first-run setup wizard.

    Args:
        launcher: AppLauncher instance.
    """
    from recall.app.bundle import ModelManager
    from recall.app.installer import FirstRunWizard
    from recall.app.permissions import PermissionManager

    print("=" * 50)
    print("Welcome to Recall!")
    print("=" * 50)
    print()

    wizard = FirstRunWizard()
    pages = wizard.get_pages()

    for page in pages:
        print(f"\n{page.title}")
        print("-" * len(page.title))
        print(page.description)
        print()

        if page.name == "model_download":
            # Check and download models
            model_manager = ModelManager()
            missing = model_manager.get_missing_models()

            if missing:
                print(f"Missing models: {[m.name for m in missing]}")
                print("Models will be downloaded on first use.")
            else:
                print("All models already downloaded!")

        elif page.name == "permissions":
            # Show permission status
            perm_manager = PermissionManager()
            print(perm_manager.get_permission_summary())

        input("Press Enter to continue...")

    # Mark setup complete
    launcher.mark_first_run_complete()
    print("\nSetup complete! Starting Recall...")


def run_model_download():
    """Run model download only."""
    from recall.app.bundle import ModelManager

    manager = ModelManager()
    missing = manager.get_missing_models()

    if not missing:
        print("All models are already downloaded!")
        return

    for model in missing:
        print(f"Downloading {model.name} ({model.size_mb} MB)...")
        try:
            manager.download_model(model)
            print(f"  ✓ {model.name} downloaded")
        except Exception as e:
            print(f"  ✗ Failed to download {model.name}: {e}")


def run_menu_bar_app():
    """Start the menu bar application."""
    try:
        from recall.app.menubar import RecallMenuBar

        app = RecallMenuBar()
        app.run()
    except ImportError as e:
        print(f"Error: Could not start menu bar app: {e}")
        print("Make sure rumps is installed (macOS only)")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Recall: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
