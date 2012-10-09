# Copyright 2012 Simon Guest
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import gobject
import pygtk
import gtk

from qlsync.engine import Device, Settings, Syncer
from qlsync.shifters_gui import ShifterSelectorWidget
from qlsync.shifters import ShifterError

class SettingsDialog(object):
    def __init__(self, settings):
        self.settings = settings
        self.window = gtk.Dialog("Settings", None, gtk.DIALOG_MODAL)
        self.window.connect("destroy", self.destroy)
        self.window.set_title("Settings")

        # overall layout
        self.layout = gtk.VBox()

        # device selector
        self.deviceTable = gtk.Table(rows=4,columns=2)

        self.deviceNameLabel = gtk.Label("Device Name")
        self.deviceNameEntry = gtk.Entry(max = 20)
        self.deviceTable.attach(self.deviceNameLabel, left_attach=0, right_attach=1, top_attach=0, bottom_attach=1)
        self.deviceTable.attach(self.deviceNameEntry, left_attach=1, right_attach=2, top_attach=0, bottom_attach=1)
        self.deviceNameLabel.show()
        self.deviceNameEntry.show()

        self.deviceMusicdirLabel = gtk.Label("Music Directory")
        self.deviceMusicdirEntry = gtk.Entry(max = 40)
        self.deviceTable.attach(self.deviceMusicdirLabel, left_attach=0, right_attach=1, top_attach=1, bottom_attach=2)
        self.deviceTable.attach(self.deviceMusicdirEntry, left_attach=1, right_attach=2, top_attach=1, bottom_attach=2)
        self.deviceMusicdirLabel.show()
        self.deviceMusicdirEntry.show()

        self.deviceFlattenButton = gtk.CheckButton("Flatten directories")
        self.deviceTable.attach(self.deviceFlattenButton, left_attach=1, right_attach=2, top_attach=2, bottom_attach=3)
        self.deviceFlattenButton.show()

        self.layout.pack_start(self.deviceTable)
        self.deviceTable.show()

        # shifter selector
        self.shifterSettings = ShifterSelectorWidget()
        self.layout.pack_start(self.shifterSettings)
        self.shifterSettings.show()

        # buttons
        self.buttonBox = gtk.HBox()
        # cancel button
        cancelButton = gtk.Button("Cancel")
        cancelButton.connect_object("clicked", self.destroy, self.window)
        self.buttonBox.pack_start(cancelButton)
        cancelButton.show()
        # delete button
        deleteButton = gtk.Button("Delete")
        deleteButton.connect_object("clicked", self.delete_callback, self.window)
        self.buttonBox.pack_start(deleteButton)
        deleteButton.show()
        # ok button
        okButton = gtk.Button("OK")
        okButton.connect_object("clicked", self.ok_callback, self.window)
        self.buttonBox.pack_start(okButton)
        okButton.show()
        okButton.set_flags(gtk.CAN_DEFAULT)
        okButton.grab_default()
        self.layout.pack_start(self.buttonBox)
        self.buttonBox.show()

        self.window.action_area.pack_start(self.layout)
        self.layout.show()

    def destroy(self, widget=None):
        self.window.hide()

    def show(self, deviceIndex):
        self.deviceIndex = deviceIndex
        self.display()
        self.window.show()

    def display(self):
        if self.deviceIndex != None:
            device = self.settings.devices[self.deviceIndex]
            self.deviceNameEntry.set_text(device.name)
            self.deviceMusicdirEntry.set_text(device.musicdir)
            self.deviceFlattenButton.set_active(device.flatten)
            self.shifterSettings.display(device.shifter)
        else:
            self.clear()

    def clear(self):
        self.deviceNameEntry.set_text("")
        self.deviceMusicdirEntry.set_text("")
        self.deviceFlattenButton.set_active(False)
        
        self.shifterSettings.clear()

    def create_device(self):
        shifter = self.shifterSettings.create_shifter()
        name = self.deviceNameEntry.get_text().strip()
        musicdir = self.deviceMusicdirEntry.get_text().strip()
        flatten = self.deviceFlattenButton.get_active()
        device = Device(name, musicdir, shifter, flatten)
        return device

    def delete_callback(self, data=None):
        if self.deviceIndex != None:
            self.settings.delete_device(self.deviceIndex)
        self.destroy()

    def ok_callback(self, data=None):
        self.settings.store_device(self.create_device(), self.deviceIndex)
        self.destroy()

class MainWindow(object):
    def __init__(self):
        self.syncer = Syncer()
        self.settings = Settings()
        self.settingsDialog = SettingsDialog(self.settings)

        # create a new dialog window
        self.window = gtk.Dialog()
        self.window.connect("destroy", self.destroy)
        self.window.set_title("qlsync")
        self.window.set_border_width(0)
        self.window.set_geometry_hints(min_height = 500)
        # create a new scrolled window.
        scrolled_window = gtk.ScrolledWindow(hadjustment = None)
        scrolled_window.set_border_width(10)
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        # The dialog window is created with a vbox packed into it.
        self.window.vbox.pack_start(scrolled_window)
        scrolled_window.show()
    
        # playlists table
        self.playlist_table = gtk.Table()
        self.playlist_table.set_row_spacings(10)
        scrolled_window.add_with_viewport(self.playlist_table)
        self.playlist_checkbuttons = []
        self.display_playlists()
        self.playlist_table.show()
        self.syncer.watch_playlists(self.display_playlists)
        self.syncer.watch_playlists_on_device(self.display_playlists_status)

        # Device selection and settings button
        self.settingsButton = gtk.Button()
        self.settingsButton.connect_object("event", self.settings_callback, None)
        self.update_settings_button()
        self.window.action_area.pack_start(self.settingsButton)
        self.settingsButton.show()
        self.settings.watch_current_device(self.update_settings_button)

        # Scan button
        self.scanButton = gtk.Button("Scan")
        self.scanButton.connect_object("clicked", self.scan_callback, self.window)
        self.window.action_area.pack_start(self.scanButton)
        self.scanButton.show()

        # Sync button
        self.syncButton = gtk.Button("Sync")
        self.syncButton.connect_object("clicked", self.sync_callback, self.window)
        self.syncButton.set_flags(gtk.CAN_DEFAULT) # this makes it so the button is the default.
        self.syncButton.grab_default()
        self.window.action_area.pack_start(self.syncButton)
        self.syncButton.show()

        # Device menu
        self.create_device_menu()
        self.settings.watch_device_list(self.create_device_menu)

        self.set_sync_sensitive(False)

        # that's all, now show it
        self.window.show()

    def destroy(self, widget):
        self.syncer.cleanup()
        gtk.main_quit()

    def show_error_message(self, message):
        md = gtk.MessageDialog(self.window, 
                               gtk.DIALOG_DESTROY_WITH_PARENT,
                               gtk.MESSAGE_ERROR, 
                               gtk.BUTTONS_CLOSE,
                               message)
        md.run()
        md.destroy()

    def update_settings_button(self):
        """Make the settings button display the current device name."""
        i = self.settings.currentDeviceIndex
        if i != None:
            text = self.settings.devices[i].name
        else:
            text = "Device ..."
        self.settingsButton.set_label(text)
        self.set_sync_sensitive(False)

    def display_playlists(self):
        n_playlists = len(self.syncer.playlist_names)
        self.playlist_table.resize(1, n_playlists)
        # delete any surplus checkbuttons
        while len(self.playlist_checkbuttons) > n_playlists:
            button = self.playlist_checkbuttons.pop()
            button.destroy()
        # add checkbuttons as needed
        while len(self.playlist_checkbuttons) < n_playlists:
            i = len(self.playlist_checkbuttons)
            button = gtk.CheckButton("")
            button.connect("toggled", self.playlist_checkbox_callback, i)
            self.playlist_table.attach(button, 0, 1, i, i+1)
            button.show()
            self.playlist_checkbuttons.append(button)
        # fix up labels
        for i in range(n_playlists):
            self.playlist_checkbuttons[i].set_label(self.syncer.playlist_names[i])

    def display_playlists_status(self):
        n_playlists = len(self.syncer.playlists_on_device)
        self.playlists_wanted = self.syncer.playlists_on_device
        for i in range(n_playlists):
            self.playlist_checkbuttons[i].set_active(self.playlists_wanted[i])

    def set_sync_sensitive(self, sensitive):
        # cope with out-of-order initialization
        if hasattr(self, "syncButton"):
            self.syncButton.set_sensitive(sensitive)
        if hasattr(self, "playlist_checkbuttons"):
            for b in self.playlist_checkbuttons:
                b.set_sensitive(sensitive)
        
    def playlist_checkbox_callback(self, widget, i):
        wanted = (False, True)[widget.get_active()]
        self.playlists_wanted[i] = wanted

    def settings_callback(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.deviceMenu.popup(None, None, None, event.button, event.time)
            #self.settingsDialog.show()

    def device_callback(self, widget, data=None):
        if data < 0:
            deviceIndex = None
        else:
            deviceIndex = data
        self.settingsDialog.show(deviceIndex)

    def scan_callback(self, widget):
        self.syncer.scan_library()
        if self.settings.currentDeviceIndex != None:
            device = self.settings.devices[self.settings.currentDeviceIndex]
            try:
                self.syncer.scan_device(device)
                self.set_sync_sensitive(True)
            except ShifterError as e:
                self.show_error_message(str(e))

    def sync_callback(self, widget):
        if self.settings.currentDeviceIndex != None:
            device = self.settings.devices[self.settings.currentDeviceIndex]

            # progress window is TBD
            self.progress_window = gtk.Dialog("qlsync progress", None, gtk.DIALOG_MODAL)
            progress_vbox = gtk.VBox()

            # label
            self.progress_label = gtk.Label("")
            progress_vbox.pack_start(self.progress_label)
            self.progress_label.show()

            # progress bar
            self.progress_bar = gtk.ProgressBar()
            progress_vbox.pack_start(self.progress_bar)
            self.progress_bar.show()

            # cancel button
            cancelButton = gtk.Button("Cancel")
            cancelButton.connect_object("clicked", self.cancel_sync_callback, self.window)
            progress_vbox.pack_start(cancelButton)
            cancelButton.show()

            self.progress_window.action_area.pack_start(progress_vbox)
            progress_vbox.show()
            self.progress_window.show()

            try:
                self.syncer.sync_device(device,
                                        self.playlists_wanted,
                                        self.update_progress_label_callback,
                                        self.update_progress_callback)
            except ShifterError as e:
                self.show_error_message(str(e))

    def cancel_sync_callback(self, widget):
        self.syncer.cancel_sync()

    def update_progress_label_callback(self, text):
        gobject.idle_add(self.update_progress_label, text)

    def update_progress_label(self, text):
        self.progress_label.set_text(text)

    def update_progress_callback(self, fraction, done=False):
        gobject.idle_add(self.update_progress, fraction, done)

    def update_progress(self, fraction, done=False):
        self.progress_bar.set_fraction(fraction)
        if done:
            device = self.settings.devices[self.settings.currentDeviceIndex]
            self.syncer.sync_device_completed(fraction, device)
            self.close_progress_window()

    def close_progress_window(self):
            self.progress_window.destroy()
            self.progress_window = None
            self.progress_bar = None
            self.progress_label = None

    def create_device_menu(self):
        self.deviceMenu = gtk.Menu()
        i = 0
        for name in ['New ...'] + [ d.name for d in self.settings.devices ]:
            item = gtk.MenuItem(name)
            item.connect("activate", self.device_callback, i - 1)
            self.deviceMenu.append(item)
            item.show()
            i += 1
        self.set_sync_sensitive(False)
