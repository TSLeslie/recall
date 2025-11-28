#!/usr/bin/env python3
"""Minimal test for menu bar app."""
import rumps

class TestMenuBar(rumps.App):
    def __init__(self):
        super().__init__("Test", title="🎤")
        self.menu = [
            rumps.MenuItem("Start Recording", callback=self.start),
            rumps.MenuItem("Stop Recording", callback=self.stop),
            None,  # Separator
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
    
    def start(self, sender):
        self.title = "🔴"
        rumps.notification("Recall", "Recording", "Started recording")
    
    def stop(self, sender):
        self.title = "🎤"
        rumps.notification("Recall", "Recording", "Stopped recording")

if __name__ == "__main__":
    print("Starting test menu bar app...")
    print("Look for 🎤 in your menu bar!")
    print("Press Ctrl+C to quit")
    app = TestMenuBar()
    app.run()
