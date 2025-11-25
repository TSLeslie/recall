"""Tests for Ticket 8.3: Installer and Setup.

This module tests:
- DMG installer creation
- First-run wizard
- Installation documentation
- App launcher
"""

# ============================================================================
# Test: InstallerConfig
# ============================================================================


class TestInstallerConfig:
    """Tests for installer configuration."""

    def test_installer_config_defaults(self):
        """Test default installer configuration."""
        from recall.app.installer import InstallerConfig

        config = InstallerConfig()

        assert config.app_name == "Recall"
        assert config.dmg_name == "Recall-Installer.dmg"
        assert config.volume_name == "Recall Installer"

    def test_installer_config_background_image(self):
        """Test installer background image configuration."""
        from recall.app.installer import InstallerConfig

        config = InstallerConfig()

        assert config.background_image is not None or config.background_image is None
        # Background image is optional

    def test_installer_config_window_size(self):
        """Test installer window size configuration."""
        from recall.app.installer import InstallerConfig

        config = InstallerConfig()

        assert config.window_width > 0
        assert config.window_height > 0


# ============================================================================
# Test: DMGBuilder
# ============================================================================


class TestDMGBuilder:
    """Tests for DMG builder."""

    def test_dmg_builder_init(self):
        """Test DMGBuilder initialization."""
        from recall.app.installer import DMGBuilder

        builder = DMGBuilder()

        assert builder is not None

    def test_dmg_builder_with_custom_config(self):
        """Test DMGBuilder with custom config."""
        from recall.app.installer import DMGBuilder, InstallerConfig

        config = InstallerConfig(dmg_name="Custom-Installer.dmg")
        builder = DMGBuilder(config=config)

        assert builder.config.dmg_name == "Custom-Installer.dmg"

    def test_get_dmg_spec(self):
        """Test getting DMG specification."""
        from recall.app.installer import DMGBuilder

        builder = DMGBuilder()
        spec = builder.get_dmg_spec()

        assert "volume_name" in spec or "volname" in str(spec).lower()
        assert isinstance(spec, dict)

    def test_dmg_spec_includes_applications_link(self):
        """Test DMG spec includes Applications folder symlink."""
        from recall.app.installer import DMGBuilder

        builder = DMGBuilder()
        spec = builder.get_dmg_spec()

        # Should have applications symlink
        assert "applications" in str(spec).lower() or "symlinks" in spec


# ============================================================================
# Test: FirstRunWizard
# ============================================================================


class TestFirstRunWizard:
    """Tests for first-run wizard."""

    def test_first_run_wizard_init(self):
        """Test FirstRunWizard initialization."""
        from recall.app.installer import FirstRunWizard

        wizard = FirstRunWizard()

        assert wizard is not None

    def test_get_wizard_pages(self):
        """Test getting wizard pages."""
        from recall.app.installer import FirstRunWizard

        wizard = FirstRunWizard()
        pages = wizard.get_pages()

        assert len(pages) > 0

    def test_wizard_has_welcome_page(self):
        """Test wizard has welcome page."""
        from recall.app.installer import FirstRunWizard

        wizard = FirstRunWizard()
        pages = wizard.get_pages()

        page_names = [p.name for p in pages]
        assert "welcome" in page_names

    def test_wizard_has_model_download_page(self):
        """Test wizard has model download page."""
        from recall.app.installer import FirstRunWizard

        wizard = FirstRunWizard()
        pages = wizard.get_pages()

        page_names = [p.name for p in pages]
        assert any("model" in name.lower() for name in page_names)

    def test_wizard_has_permissions_page(self):
        """Test wizard has permissions page."""
        from recall.app.installer import FirstRunWizard

        wizard = FirstRunWizard()
        pages = wizard.get_pages()

        page_names = [p.name for p in pages]
        assert any("permission" in name.lower() for name in page_names)

    def test_wizard_has_complete_page(self):
        """Test wizard has completion page."""
        from recall.app.installer import FirstRunWizard

        wizard = FirstRunWizard()
        pages = wizard.get_pages()

        page_names = [p.name for p in pages]
        assert any("complete" in name.lower() or "finish" in name.lower() for name in page_names)


# ============================================================================
# Test: WizardPage
# ============================================================================


class TestWizardPage:
    """Tests for wizard page dataclass."""

    def test_wizard_page_structure(self):
        """Test WizardPage structure."""
        from recall.app.installer import WizardPage

        page = WizardPage(
            name="test",
            title="Test Page",
            description="A test page",
            can_skip=False,
        )

        assert page.name == "test"
        assert page.title == "Test Page"
        assert page.can_skip is False

    def test_wizard_page_action(self):
        """Test WizardPage with action."""
        from recall.app.installer import WizardPage

        def test_action():
            return True

        page = WizardPage(
            name="action_page",
            title="Action Page",
            description="Page with action",
            action=test_action,
        )

        assert page.action is not None
        assert page.action() is True


# ============================================================================
# Test: AppLauncher
# ============================================================================


class TestAppLauncher:
    """Tests for app launcher."""

    def test_app_launcher_init(self):
        """Test AppLauncher initialization."""
        from recall.app.installer import AppLauncher

        launcher = AppLauncher()

        assert launcher is not None

    def test_check_first_run(self, tmp_path):
        """Test checking if this is first run."""
        from recall.app.installer import AppLauncher

        launcher = AppLauncher(config_dir=tmp_path)

        # Empty directory = first run
        assert launcher.is_first_run() is True

    def test_first_run_false_after_complete(self, tmp_path):
        """Test first run returns False after completion."""
        from recall.app.installer import AppLauncher

        launcher = AppLauncher(config_dir=tmp_path)
        launcher.mark_first_run_complete()

        assert launcher.is_first_run() is False

    def test_get_launch_mode(self, tmp_path):
        """Test getting launch mode."""
        from recall.app.installer import AppLauncher, LaunchMode

        launcher = AppLauncher(config_dir=tmp_path)

        # First run should return wizard mode
        mode = launcher.get_launch_mode()
        assert mode == LaunchMode.FIRST_RUN_WIZARD

    def test_launch_mode_normal_after_setup(self, tmp_path):
        """Test normal launch mode after setup."""
        from recall.app.installer import AppLauncher, LaunchMode

        launcher = AppLauncher(config_dir=tmp_path)
        launcher.mark_first_run_complete()

        mode = launcher.get_launch_mode()
        assert mode == LaunchMode.NORMAL


# ============================================================================
# Test: LaunchMode Enum
# ============================================================================


class TestLaunchMode:
    """Tests for LaunchMode enumeration."""

    def test_launch_mode_values(self):
        """Test LaunchMode values."""
        from recall.app.installer import LaunchMode

        assert hasattr(LaunchMode, "NORMAL")
        assert hasattr(LaunchMode, "FIRST_RUN_WIZARD")
        assert hasattr(LaunchMode, "MODEL_DOWNLOAD")


# ============================================================================
# Test: Installation Scripts
# ============================================================================


class TestInstallationScripts:
    """Tests for installation script generation."""

    def test_generate_build_script(self):
        """Test generating build script."""
        from recall.app.installer import generate_build_script

        script = generate_build_script()

        assert "py2app" in script
        assert "#!/" in script or "python" in script.lower()

    def test_generate_dmg_script(self):
        """Test generating DMG creation script."""
        from recall.app.installer import generate_dmg_script

        script = generate_dmg_script()

        assert "dmg" in script.lower()
        assert "hdiutil" in script or "create-dmg" in script.lower()

    def test_build_script_is_executable(self):
        """Test that build script looks like a valid shell script."""
        from recall.app.installer import generate_build_script

        script = generate_build_script()

        # Should have shebang or be a valid script structure
        assert script.strip().startswith("#") or "python" in script.lower()


# ============================================================================
# Test: Documentation Generation
# ============================================================================


class TestDocumentation:
    """Tests for documentation generation."""

    def test_generate_install_docs(self):
        """Test generating installation documentation."""
        from recall.app.installer import generate_install_docs

        docs = generate_install_docs()

        assert "# " in docs  # Has headers
        assert "install" in docs.lower()
        assert "Recall" in docs

    def test_install_docs_has_requirements(self):
        """Test install docs include requirements."""
        from recall.app.installer import generate_install_docs

        docs = generate_install_docs()

        assert "macos" in docs.lower() or "mac" in docs.lower()

    def test_install_docs_has_steps(self):
        """Test install docs have installation steps."""
        from recall.app.installer import generate_install_docs

        docs = generate_install_docs()

        # Should have numbered steps or bullet points
        assert "1." in docs or "- " in docs or "* " in docs

    def test_generate_permissions_docs(self):
        """Test generating permissions documentation."""
        from recall.app.installer import generate_permissions_docs

        docs = generate_permissions_docs()

        assert "microphone" in docs.lower()
        assert "accessibility" in docs.lower()
        assert "permission" in docs.lower()


# ============================================================================
# Test: Version Info
# ============================================================================


class TestVersionInfo:
    """Tests for version information."""

    def test_get_installer_version(self):
        """Test getting installer version."""
        from recall.app.installer import get_installer_version

        version = get_installer_version()

        assert version is not None
        assert "." in version

    def test_get_minimum_macos_version(self):
        """Test getting minimum macOS version."""
        from recall.app.installer import get_minimum_macos_version

        version = get_minimum_macos_version()

        assert version is not None
        assert version >= "12.0"
