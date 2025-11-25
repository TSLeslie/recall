#!/usr/bin/env python3
"""Sprint 7 Demo: Packaging & Distribution.

This demo showcases the packaging and distribution features:
- Ticket 8.1: macOS App Bundle (py2app configuration)
- Ticket 8.2: Permissions Handling
- Ticket 8.3: Installer and Setup

Run with: python examples/sprint7_packaging_demo.py
"""

import tempfile
from pathlib import Path


def main():
    """Run Sprint 7 packaging demo."""
    print("=" * 60)
    print("Sprint 7 Demo: Packaging & Distribution")
    print("=" * 60)
    print()

    demo_app_bundle()
    demo_permissions()
    demo_installer()
    demo_documentation()

    print()
    print("=" * 60)
    print("Sprint 7 Demo Complete!")
    print("=" * 60)


def demo_app_bundle():
    """Demo Ticket 8.1: macOS App Bundle."""
    print("\n" + "=" * 60)
    print("Ticket 8.1: macOS App Bundle")
    print("=" * 60)

    from recall.app.bundle import (
        AppConfig,
        FirstRunSetup,
        ModelManager,
        generate_setup_py,
        get_bundle_info,
        get_py2app_options,
    )

    # App Configuration
    print("\n1. App Configuration")
    print("-" * 40)
    config = AppConfig()
    print(f"   App Name: {config.app_name}")
    print(f"   Bundle ID: {config.bundle_identifier}")
    print(f"   Version: {config.version}")
    print(f"   Min macOS: {config.min_macos_version}")
    print(f"   Icon: {config.icon_name}")

    # Bundle Info (Info.plist)
    print("\n2. Bundle Info (Info.plist)")
    print("-" * 40)
    info = get_bundle_info()
    for key in ["CFBundleName", "CFBundleIdentifier", "CFBundleVersion", "LSMinimumSystemVersion"]:
        print(f"   {key}: {info[key]}")

    # py2app Options
    print("\n3. py2app Build Options")
    print("-" * 40)
    options = get_py2app_options()
    py2app = options["py2app"]
    print(f"   Packages: {len(py2app['packages'])} included")
    print(f"   Excludes: {len(py2app['excludes'])} excluded")
    print(f"   Includes: {py2app['includes']}")

    # Model Manager
    print("\n4. Model Manager")
    print("-" * 40)
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = ModelManager(models_dir=Path(tmp_dir))
        required = manager.get_required_models()
        print(f"   Required models: {len(required)}")
        for model in required:
            print(f"   - {model.name}: {model.filename} ({model.size_mb} MB)")

        missing = manager.get_missing_models()
        print(f"   Missing models: {len(missing)}")

    # First Run Setup
    print("\n5. First Run Setup")
    print("-" * 40)
    with tempfile.TemporaryDirectory() as tmp_dir:
        setup = FirstRunSetup(config_dir=Path(tmp_dir))
        print(f"   Is first run: {setup.is_first_run()}")

        steps = setup.get_setup_steps()
        print(f"   Setup steps: {len(steps)}")
        for step in steps:
            print(f"   - {step.name}: {step.title}")

        setup.mark_setup_complete()
        print(f"   After marking complete: {setup.is_first_run()}")


def demo_permissions():
    """Demo Ticket 8.2: Permissions Handling."""
    print("\n" + "=" * 60)
    print("Ticket 8.2: Permissions Handling")
    print("=" * 60)

    from recall.app.permissions import (
        PermissionManager,
        PermissionStatus,
        PermissionType,
        get_permission_instructions,
        get_preferences_url,
    )

    # Permission Types
    print("\n1. Permission Types")
    print("-" * 40)
    for perm_type in PermissionType:
        print(f"   {perm_type.name}: {perm_type.value}")

    # Permission Status
    print("\n2. Permission Status Values")
    print("-" * 40)
    for status in PermissionStatus:
        print(f"   {status.name}: {status.value}")

    # Permission Manager
    print("\n3. Permission Manager")
    print("-" * 40)
    manager = PermissionManager()
    permissions = manager.get_all_permissions()
    print(f"   Total permissions: {len(permissions)}")
    for perm in permissions:
        required = "required" if perm.required else "optional"
        print(f"   - {perm.permission_type.value}: {perm.status.value} ({required})")

    # Permission Summary
    print("\n4. Permission Summary")
    print("-" * 40)
    summary = manager.get_permission_summary()
    for line in summary.split("\n"):
        print(f"   {line}")

    # System Preferences URLs
    print("\n5. System Preferences URLs")
    print("-" * 40)
    for perm_type in PermissionType:
        url = get_preferences_url(perm_type)
        print(f"   {perm_type.value}:")
        print(f"     {url}")

    # Permission Instructions
    print("\n6. Sample Instructions (Microphone)")
    print("-" * 40)
    instructions = get_permission_instructions(PermissionType.MICROPHONE)
    for line in instructions.split("\n")[:5]:
        print(f"   {line}")


def demo_installer():
    """Demo Ticket 8.3: Installer and Setup."""
    print("\n" + "=" * 60)
    print("Ticket 8.3: Installer and Setup")
    print("=" * 60)

    from recall.app.installer import (
        AppLauncher,
        DMGBuilder,
        FirstRunWizard,
        InstallerConfig,
        LaunchMode,
        generate_build_script,
        generate_dmg_script,
    )

    # Installer Configuration
    print("\n1. Installer Configuration")
    print("-" * 40)
    config = InstallerConfig()
    print(f"   App Name: {config.app_name}")
    print(f"   DMG Name: {config.dmg_name}")
    print(f"   Volume Name: {config.volume_name}")
    print(f"   Window Size: {config.window_width}x{config.window_height}")

    # DMG Builder
    print("\n2. DMG Builder Spec")
    print("-" * 40)
    builder = DMGBuilder()
    spec = builder.get_dmg_spec()
    print(f"   Volume: {spec['volume_name']}")
    print(f"   Format: {spec['format']}")
    print(f"   Contents: {len(spec['contents'])} items")
    print(f"   Symlinks: {spec['symlinks']}")

    # First Run Wizard
    print("\n3. First Run Wizard")
    print("-" * 40)
    wizard = FirstRunWizard()
    pages = wizard.get_pages()
    print(f"   Total pages: {len(pages)}")
    for page in pages:
        skip = "(skippable)" if page.can_skip else ""
        print(f"   - {page.name}: {page.title} {skip}")

    # App Launcher
    print("\n4. App Launcher")
    print("-" * 40)
    with tempfile.TemporaryDirectory() as tmp_dir:
        launcher = AppLauncher(config_dir=Path(tmp_dir))
        print(f"   Is first run: {launcher.is_first_run()}")
        print(f"   Launch mode: {launcher.get_launch_mode().value}")

        launcher.mark_first_run_complete()
        print(f"   After setup complete:")
        print(f"   Is first run: {launcher.is_first_run()}")
        print(f"   Launch mode: {launcher.get_launch_mode().value}")

    # Launch Modes
    print("\n5. Launch Modes")
    print("-" * 40)
    for mode in LaunchMode:
        print(f"   {mode.name}: {mode.value}")

    # Build Scripts
    print("\n6. Build Scripts (previews)")
    print("-" * 40)
    build_script = generate_build_script()
    print("   build_app.sh preview:")
    for line in build_script.split("\n")[1:5]:
        print(f"   {line}")

    dmg_script = generate_dmg_script()
    print("\n   create_dmg.sh preview:")
    for line in dmg_script.split("\n")[1:5]:
        print(f"   {line}")


def demo_documentation():
    """Demo documentation generation."""
    print("\n" + "=" * 60)
    print("Documentation Generation")
    print("=" * 60)

    from recall.app.installer import (
        generate_install_docs,
        generate_permissions_docs,
        get_installer_version,
        get_minimum_macos_version,
    )

    # Version Info
    print("\n1. Version Information")
    print("-" * 40)
    print(f"   Installer Version: {get_installer_version()}")
    print(f"   Min macOS Version: {get_minimum_macos_version()}")

    # Install Documentation
    print("\n2. Installation Documentation")
    print("-" * 40)
    install_docs = generate_install_docs()
    lines = install_docs.split("\n")
    print(f"   Total lines: {len(lines)}")
    print("   Preview (first 10 lines):")
    for line in lines[:10]:
        print(f"   {line}")

    # Permissions Documentation
    print("\n3. Permissions Documentation")
    print("-" * 40)
    perm_docs = generate_permissions_docs()
    lines = perm_docs.split("\n")
    print(f"   Total lines: {len(lines)}")
    print("   Preview (first 10 lines):")
    for line in lines[:10]:
        print(f"   {line}")

    # File locations
    print("\n4. Documentation Files Created")
    print("-" * 40)
    print("   docs/INSTALL.md - Installation guide")
    print("   docs/PERMISSIONS.md - Permissions guide")


if __name__ == "__main__":
    main()
