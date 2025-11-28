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

    # Detect project directory (if running from source)
    project_dir = Path(__file__).parent.parent.parent.parent
    if not (project_dir / "models").exists():
        project_dir = None

    # Check launch mode
    launcher = AppLauncher(project_dir=project_dir)
    mode = launcher.get_launch_mode()

    if mode == LaunchMode.FIRST_RUN_WIZARD:
        run_first_run_wizard(launcher)
    elif mode == LaunchMode.MODEL_DOWNLOAD:
        run_model_download(launcher)

    # Start the menu bar app
    run_menu_bar_app()


def run_first_run_wizard(launcher):
    """Run the first-run setup wizard.

    Args:
        launcher: AppLauncher instance with model_manager.
    """
    from recall.app.bundle import ModelSetupChoice
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
            handle_model_setup(launcher)

        elif page.name == "permissions":
            # Show permission status
            perm_manager = PermissionManager()
            print(perm_manager.get_permission_summary())

        input("Press Enter to continue...")

    # Mark setup complete
    launcher.mark_first_run_complete()
    print("\nSetup complete! Starting Recall...")


def handle_model_setup(launcher):
    """Handle model discovery and setup.

    Args:
        launcher: AppLauncher instance with model_manager.
    """
    from recall.app.bundle import ModelSetupChoice

    model_manager = launcher.model_manager

    # First, check for existing models
    status = model_manager.get_model_status()
    found = status["found"]
    missing = status["missing"]

    if found:
        print("\n✓ Found existing models:")
        for model in found:
            print(f"  • {model.name}: {model.found_path}")

    if not missing:
        print("\n✓ All required models are available!")
        return

    print(f"\n⚠ Missing models:")
    for model in missing:
        print(f"  • {model.name} ({model.size_mb} MB)")

    # Ask user what to do
    choice = model_manager.prompt_download_or_locate()

    if choice == ModelSetupChoice.LOCATE_EXISTING:
        custom_path = model_manager.prompt_for_model_path()
        if custom_path:
            launcher.set_models_path(custom_path)
            print(f"\n✓ Added model path: {custom_path}")

            # Re-check for models
            new_status = model_manager.get_model_status()
            if new_status["found"]:
                print("\n✓ Found models:")
                for model in new_status["found"]:
                    print(f"  • {model.name}: {model.found_path}")

            if new_status["missing"]:
                print("\n⚠ Still missing:")
                for model in new_status["missing"]:
                    print(f"  • {model.name}")
                print("\nThese will be downloaded on first use.")
        else:
            print("\nNo valid path provided. Models will be downloaded on first use.")

    elif choice == ModelSetupChoice.DOWNLOAD:
        download_models(model_manager, missing)

    else:  # SKIP
        print("\nSkipping model setup. Models will be downloaded on first use.")


def download_models(model_manager, models):
    """Download the specified models with progress.

    Args:
        model_manager: ModelManager instance.
        models: List of ModelInfo to download.
    """
    print("\nDownloading models...")

    for model in models:
        print(f"\nDownloading {model.name} ({model.size_mb} MB)...")
        try:
            path = model_manager.download_model(model)
            print(f"  ✓ {model.name} downloaded to {path}")
        except Exception as e:
            print(f"  ✗ Failed to download {model.name}: {e}")
            print("    You can try again later or download manually.")


def run_model_download(launcher):
    """Run model download only.

    Args:
        launcher: AppLauncher instance with model_manager.
    """
    model_manager = launcher.model_manager
    missing = model_manager.get_missing_models()

    if not missing:
        print("All models are already downloaded!")
        return

    download_models(model_manager, missing)


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
