import sys
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QInputDialog, QMessageBox

def popup_request_path():
    # Creating a QApplication if one doesn't already exist.
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # Create a temporary widget to anchor dialogs.
    widget = QWidget()

    # Ask for the directory
    directory = QFileDialog.getExistingDirectory(widget, "Select Directory")
    if not directory:
        QMessageBox.information(widget, "Information", "No directory selected.")
        return

    # Ask for a filename
    filename, ok = QInputDialog.getText(widget, "Filename", "Enter filename:")
    if not ok or not filename:
        QMessageBox.information(widget, "Information", "No filename provided.")
        return

    # Combine the directory and filename into a full path
    snapshot_path = f"{directory}/{filename}"
    return snapshot_path

# Example usage - this can be connected to your snapshot button's clicked signal.
if __name__ == "__main__":
    popup_request_path()