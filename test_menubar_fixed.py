#!/usr/bin/env python3
"""Test menu bar with proper macOS app activation."""
import sys

# IMPORTANT: Set activation policy BEFORE importing rumps
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
NSApplication.sharedApplication()
NSApp = NSApplication.sharedApplication()
NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

import rumps

class TestMenuBar(rumps.App):
    def __init__(self):
        super().__init__("Test", title="🎤", quit_button=None)
        self.menu = [
            rumps.MenuItem("Start Recording", callback=self.start),
            rumps.MenuItem("Stop Recording", callback=self.stop),
            None,
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]
    
    def start(self, sender):
        self.title = "🔴"
        rumps.notification("Recall", "Recording", "Started recording")
    
    def stop(self, sender):
        self.title = "🎤"
        rumps.notification("Recall", "Recording", "Stopped recording")
    
    def quit_app(self, sender):
        rumps.quit_application()

if __name__ == "__main__":
    print("Starting menu bar app with proper activation policy...")
    print("Look for 🎤 in your menu bar!")
    app = TestMenuBar()
    app.run()
