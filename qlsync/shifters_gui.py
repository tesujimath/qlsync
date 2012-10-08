# Copyright 2012 Simon Guest
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import pygtk
import gtk

from qlsync.shifters import *

class FilesystemShifterWidget(gtk.VBox):
    def __init__(self):
        pass

    def display(self, shifter):
        pass

    def create_shifter(self):
        return FilesystemShifter()

    def clear(self):
        pass


class FtpShifterWidget(gtk.VBox):
    """Settings GUI for FTP."""

    def __init__(self, *args):
        super(FtpShifterWidget, self).__init__(args)

        self.hostBox = gtk.HBox()
        self.hostLabel = gtk.Label("Host")
        self.hostEntry = gtk.Entry()
        self.hostBox.pack_start(self.hostLabel)
        self.hostBox.pack_start(self.hostEntry)
        self.hostLabel.show()
        self.hostEntry.show()
        self.pack_start(self.hostBox)
        self.hostBox.show()

        self.userBox = gtk.HBox()
        self.userLabel = gtk.Label("User")
        self.userEntry = gtk.Entry()
        self.userBox.pack_start(self.userLabel)
        self.userBox.pack_start(self.userEntry)
        self.userLabel.show()
        self.userEntry.show()
        self.pack_start(self.userBox)
        self.userBox.show()

        self.passwordBox = gtk.HBox()
        self.passwordLabel = gtk.Label("Password")
        self.passwordEntry = gtk.Entry()
        self.passwordBox.pack_start(self.passwordLabel)
        self.passwordBox.pack_start(self.passwordEntry)
        self.passwordLabel.show()
        self.passwordEntry.show()
        self.pack_start(self.passwordBox)
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

class ShifterSelectorWidget(gtk.HBox):
    """Widget for selecting shifter, and defining parameters."""

    def __init__(self, *args):
        super(ShifterSelectorWidget, self).__init__(args)

        # shifter widgets
        self.shifterWidgets = []
        self.indexByClass = {}
        self.currentShifter = 0         # index into shifterWidgets

        # radiobuttons for selecting shifter
        self.radioBox = gtk.VBox()
        self.pack_start(self.radioBox)
        self.radioBox.show()

        # shifter selectors
        self.shifterButtons = []
        i_shifter = 0

        # filesystem shifter
        shifterWidget = FilesystemShifterWidget()
        self.pack_start(shifterWidget)
        self.shifterWidgets.append(shifterWidget)
        rb = gtk.RadioButton(group = None, label = "Filesystem") # only this one has group=None
        self.radioBox.pack_start(rb)
        rb.connect_object("toggled", self.shifter_selected, i_shifter)
        rb.show()
        self.shifterButtons.append(rb)
        self.indexByClass['FilesystemShifter'] = i_shifter
        i_shifter += 1

        # ftp shifter
        shifterWidget = FtpShifterWidget()
        self.pack_start(shifterWidget)
        self.shifterWidgets.append(shifterWidget)
        rb = gtk.RadioButton(group = self.shifterButtons[0], label = "FTP")
        self.radioBox.pack_start(rb)
        rb.connect_object("toggled", self.shifter_selected, i_shifter)
        rb.show()
        self.shifterButtons.append(rb)
        self.indexByClass['FtpShifter'] = i_shifter
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

