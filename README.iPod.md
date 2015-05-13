Getting music onto recent iPods without using iTunes can be tricky.
Here's how my son does it, which explains I made qlsync behave in
the way it does.

1. Jailbreak your iPod, and install MewSeek from Cydia, and vsftpd.
   To get vsftp to work, you need to install openssh, ssh into the
   device, and mkdir /usr/share/empty.

2. Now you can drop files into /var/mobile/Media/Downloads using
   qlsync.

3. Get MewSeek to import them into your iPod library.
   This removes the music files from the Downloads directory, but
   leaves the playlists there (so qlsync knows what's on the device).

4. Deletion of music really needs to be done from the iPod itself.

5. To track this, you can use the separate script
   qlsync-playlist-from-device to make a playlist listing everything
   on the device.  qlsync will see this, and not upload those songs
   again.  Use this script after you delete or add music onto the
   device without using qlsync.

I'm not really interested in iPods, so only did the minimum to keep my
son happy.  Don't expect much more from me in this area.

Simon Guest <simon.guest@tesujimath.org>
9 Oct 2012
