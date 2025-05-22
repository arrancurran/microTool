from interface.popup_notif.popup_notif import PopupNotif

class PopupNotifManager:
    def __init__(self, parent):
        self.parent = parent
        self.popup = None

    def show_popup_notif(self, message, button=None):
        # Check if the popup exists and is visible.
        if self.popup is not None and self.popup.isVisible():
            try:
                self.popup.update_popup_notif(message)
            except RuntimeError:
                # Popup was deleted, so clear the reference.
                self.popup = None

        # Create a new popup.
        self.popup = PopupNotif(message, button, self.parent)
        self.popup.destroyed.connect(self.on_popup_destroyed)
        self.popup.show()

    def on_popup_destroyed(self):
        self.popup = None