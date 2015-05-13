# Copyright 2012 Simon Guest
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

from gi.repository import Gtk

from qlsync.shifters import *

class FilesystemShifterWidget(Gtk.VBox):
    def __init__(self, error_fn, *args):
        super(FilesystemShifterWidget, self).__init__(args)
        self.error_fn = error_fn

    def display(self, shifter):
        pass

    def create_shifter(self):
        return FilesystemShifter()

    def clear(self):
        pass


class FtpShifterWidget(Gtk.VBox):
    """Settings GUI for FTP."""

    def __init__(self, error_fn, *args):
        super(FtpShifterWidget, self).__init__(args)
        self.error_fn = error_fn

        self.hostBox = Gtk.HBox()
        self.hostLabel = Gtk.Label("Host")
        self.hostEntry = Gtk.Entry()
        self.hostBox.pack_start(self.hostLabel, expand=True, fill=True, padding=0)
        self.hostBox.pack_start(self.hostEntry, expand=True, fill=True, padding=0)
        self.hostLabel.show()
        self.hostEntry.show()
        self.pack_start(self.hostBox, expand=True, fill=True, padding=0)
        self.hostBox.show()

        self.userBox = Gtk.HBox()
        self.userLabel = Gtk.Label("User")
        self.userEntry = Gtk.Entry()
        self.userBox.pack_start(self.userLabel, expand=True, fill=True, padding=0)
        self.userBox.pack_start(self.userEntry, expand=True, fill=True, padding=0)
        self.userLabel.show()
        self.userEntry.show()
        self.pack_start(self.userBox, expand=True, fill=True, padding=0)
        self.userBox.show()

        self.passwordBox = Gtk.HBox()
        self.passwordLabel = Gtk.Label("Password")
        self.passwordEntry = Gtk.Entry()
        self.passwordBox.pack_start(self.passwordLabel, expand=True, fill=True, padding=0)
        self.passwordBox.pack_start(self.passwordEntry, expand=True, fill=True, padding=0)
        self.passwordLabel.show()
        self.passwordEntry.show()
        self.pack_start(self.passwordBox, expand=True, fill=True, padding=0)
        self.passwordBox.show()
        # hide password text
        self.passwordEntry.set_visibility(False)

    def display(self, shifter):
        self.hostEntry.set_text(shifter.host)
        self.userEntry.set_text(shifter.user),
        self.passwordEntry.set_text(shifter.password)

    def create_shifter(self):
        return FtpShifter(self.hostEntry.get_text(),
                          self.userEntry.get_text(),
                          self.passwordEntry.get_text())

    def clear(self):
        self.hostEntry.set_text("")
        self.userEntry.set_text("")
        self.passwordEntry.set_text("")

class SftpShifterWidget(Gtk.VBox):
    """Settings GUI for SFTP."""

    DEFAULT_PORT = 22

    def __init__(self, error_fn, *args):
        super(SftpShifterWidget, self).__init__(args)
        self.error_fn = error_fn

        self.hostBox = Gtk.HBox()
        self.hostLabel = Gtk.Label("Host")
        self.hostEntry = Gtk.Entry()
        self.hostBox.pack_start(self.hostLabel, expand=True, fill=True, padding=0)
        self.hostBox.pack_start(self.hostEntry, expand=True, fill=True, padding=0)
        self.hostLabel.show()
        self.hostEntry.show()
        self.pack_start(self.hostBox, expand=True, fill=True, padding=0)
        self.hostBox.show()

        self.userBox = Gtk.HBox()
        self.userLabel = Gtk.Label("User")
        self.userEntry = Gtk.Entry()
        self.userBox.pack_start(self.userLabel, expand=True, fill=True, padding=0)
        self.userBox.pack_start(self.userEntry, expand=True, fill=True, padding=0)
        self.userLabel.show()
        self.userEntry.show()
        self.pack_start(self.userBox, expand=True, fill=True, padding=0)
        self.userBox.show()

        self.portBox = Gtk.HBox()
        self.portLabel = Gtk.Label("Port")
        self.portEntry = Gtk.Entry()
        self.portBox.pack_start(self.portLabel, expand=True, fill=True, padding=0)
        self.portBox.pack_start(self.portEntry, expand=True, fill=True, padding=0)
        self.portLabel.show()
        self.portEntry.show()
        self.pack_start(self.portBox, expand=True, fill=True, padding=0)
        self.portBox.show()

    def display(self, shifter):
        self.hostEntry.set_text(shifter.host)
        self.userEntry.set_text(shifter.user),
        self.portEntry.set_text(str(shifter.port))

    def create_shifter(self):
        try:
            port = int(self.portEntry.get_text())
        except ValueError:
            port = SftpShifterWidget.DEFAULT_PORT
            self.portEntry.set_text(str(port))
        return SftpShifter(self.hostEntry.get_text(),
                           self.userEntry.get_text(),
                           port)

    def clear(self):
        self.hostEntry.set_text("")
        self.userEntry.set_text("")
        self.portEntry.set_text(str(SftpShifterWidget.DEFAULT_PORT))

class AdbShifterWidget(Gtk.VBox):
    """Settings GUI for ADB."""

    def __init__(self, error_fn, *args):
        super(AdbShifterWidget, self).__init__(args)
        self.error_fn = error_fn

        self.sdcardrootBox = Gtk.HBox()
        self.sdcardrootLabel = Gtk.Label("SD card root")
        self.sdcardrootEntry = Gtk.Entry()
        self.sdcardrootBox.pack_start(self.sdcardrootLabel, expand=True, fill=True, padding=0)
        self.sdcardrootBox.pack_start(self.sdcardrootEntry, expand=True, fill=True, padding=0)
        self.sdcardrootLabel.show()
        self.sdcardrootEntry.show()
        self.pack_start(self.sdcardrootBox, expand=True, fill=True, padding=0)
        self.sdcardrootBox.show()

        self.serialBox = Gtk.HBox()
        self.serialLabel = Gtk.Label("Android serial")
        self.serialEntry = Gtk.Entry()
        self.serialBox.pack_start(self.serialLabel, expand=True, fill=True, padding=0)
        self.serialBox.pack_start(self.serialEntry, expand=True, fill=True, padding=0)
        self.serialLabel.show()
        self.serialEntry.show()
        self.pack_start(self.serialBox, expand=True, fill=True, padding=0)
        self.serialBox.show()

        self.getDeviceSerialButton = Gtk.Button("Get Device Serial")
        self.getDeviceSerialButton.connect("clicked", self.get_device_serial)
        self.pack_start(self.getDeviceSerialButton, expand=True, fill=True, padding=0)
        self.getDeviceSerialButton.show()

    def display(self, shifter):
        self.serialEntry.set_text(shifter.serial)

    def create_shifter(self):
        print("AdbShifterWidget.create_shifter()")
        return AdbShifter(self.sdcardrootEntry.get_text(), self.serialEntry.get_text())

    def clear(self):
        self.serialEntry.set_text("")

    def get_device_serial(self, evt):
        """List attached devices;  if there's just one, grab it's serial number."""
        (rc, stdout_lines, stderr_lines) = adb(["devices"])
        # strip lines, and discard empties
        stdout_lines = [line.strip() for line in stdout_lines if line.strip() != ""]
        if len(stdout_lines) == 2 and stdout_lines[0].lower().lstrip().startswith("list"):
            tokens = stdout_lines[1].split()
            if len(tokens) == 2 and tokens[1].lower() == "device":
                self.serialEntry.set_text(tokens[0])
                return
        # Failed, so give some feedback
        message = "%s\n\n%s\n%s" % ("Failed to find unique device", '\n'.join(stdout_lines), '\n'.join(stderr_lines))
        self.error_fn(message)

class ShifterSelectorWidget(Gtk.HBox):
    """Widget for selecting shifter, and defining parameters."""

    def __init__(self, error_fn, *args):
        super(ShifterSelectorWidget, self).__init__(args)

        # shifter widgets
        self.shifterWidgets = []
        self.indexByClass = {}
        self.currentShifter = 0         # index into shifterWidgets

        # radiobuttons for selecting shifter
        self.radioBox = Gtk.VBox()
        self.pack_start(self.radioBox, expand=True, fill=True, padding=0)
        self.radioBox.show()

        # shifter selectors
        self.shifterButtons = []
        i_shifter = 0

        # filesystem shifter
        shifterWidget = FilesystemShifterWidget(error_fn)
        self.pack_start(shifterWidget, expand=True, fill=True, padding=0)
        self.shifterWidgets.append(shifterWidget)
        rb = Gtk.RadioButton(group = None, label = "Filesystem") # only this one has group=None
        self.radioBox.pack_start(rb, expand=True, fill=True, padding=0)
        rb.connect_object("toggled", self.shifter_selected, i_shifter)
        rb.show()
        self.shifterButtons.append(rb)
        self.indexByClass['FilesystemShifter'] = i_shifter
        i_shifter += 1

        # ftp shifter
        shifterWidget = FtpShifterWidget(error_fn)
        self.pack_start(shifterWidget, expand=True, fill=True, padding=0)
        self.shifterWidgets.append(shifterWidget)
        rb = Gtk.RadioButton(group = self.shifterButtons[0], label = "FTP")
        self.radioBox.pack_start(rb, expand=True, fill=True, padding=0)
        rb.connect_object("toggled", self.shifter_selected, i_shifter)
        rb.show()
        self.shifterButtons.append(rb)
        self.indexByClass['FtpShifter'] = i_shifter
        i_shifter += 1

        # sftp shifter
        shifterWidget = SftpShifterWidget(error_fn)
        self.pack_start(shifterWidget, expand=True, fill=True, padding=0)
        self.shifterWidgets.append(shifterWidget)
        rb = Gtk.RadioButton(group = self.shifterButtons[0], label = "SFTP")
        self.radioBox.pack_start(rb, expand=True, fill=True, padding=0)
        rb.connect_object("toggled", self.shifter_selected, i_shifter)
        rb.show()
        self.shifterButtons.append(rb)
        self.indexByClass['SftpShifter'] = i_shifter
        i_shifter += 1

        # adb shifter
        shifterWidget = AdbShifterWidget(error_fn)
        self.pack_start(shifterWidget, expand=True, fill=True, padding=0)
        self.shifterWidgets.append(shifterWidget)
        rb = Gtk.RadioButton(group = self.shifterButtons[0], label = "ADB")
        self.radioBox.pack_start(rb, expand=True, fill=True, padding=0)
        rb.connect_object("toggled", self.shifter_selected, i_shifter)
        rb.show()
        self.shifterButtons.append(rb)
        self.indexByClass['AdbShifter'] = i_shifter
        i_shifter += 1

        self.clear()

    def shifter_selected(self, i_shifter):
        """Shifter i_shifter selected."""
        for w in self.shifterWidgets:
            w.hide()
        self.shifterWidgets[i_shifter].clear()
        self.shifterWidgets[i_shifter].show()
        self.currentShifter = i_shifter
        
    def display(self, shifter):
        i = self.indexByClass[shifter.__class__.__name__]
        self.shifterButtons[i].set_active(True)
        self.shifterWidgets[i].display(shifter)
        self.currentShifter = i

    def clear(self):
        # select first by default
        self.shifterButtons[0].set_active(True)
        self.shifter_selected(0)

    def create_shifter(self):
        return self.shifterWidgets[self.currentShifter].create_shifter()

