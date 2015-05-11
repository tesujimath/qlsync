# Copyright 2012 Simon Guest
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import filecmp
import ftplib
import os
import paramiko
import shutil

class ShifterError(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "Error: " + self.message

class FilesystemShifter(object):
    """Use the filesystem to transfer files."""
    def __init__(self):
        pass

    def __str__(self):
        return "FilesystemShifter"

    def open(self):
        pass

    def path_exists(self, dst):
        return os.path.exists(dst)

    def makedirs(self, dst):
        try:
            if not self.path_exists(dst):
                os.makedirs(dst)
        except OSError as e:
            raise ShifterError(str(e))

    def uploadfile(self, src, dst):
        try:
            shutil.copyfile(src, dst)
        except IOError as e:
            raise ShifterError(str(e))

    def readlines(self, src):
        lines = []
        try:
            f = open(src, 'r')
            for line in f:
                lines.append(line.rstrip('\n'))
            f.close()
        except IOError as e:
            raise ShifterError(str(e))
        return lines

    def removefile(self, dst):
        try:
            os.remove(dst)
        except OSError as e:
            raise ShifterError(str(e))

    def removedir_if_empty(self, dst):
        try:
            os.rmdir(dst)
        except OSError:
            # wasn't empty, so ignore
            pass

    def ls(self, dst):
        """Return directory listing."""
        try:
            files = os.listdir(dst)
        except OSError as e:
             raise ShifterError(str(e))
        return files

    def close(self):
        # ensure everything is on the disk
        os.system("sync")


class FtpShifter(object):
    """Use ftp to transfer files."""
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def __str__(self):
        return "FtpShifter(host=" + self.host + ",user=" + self.user + ")"

    def open(self):
        try:
            self.ftp = ftplib.FTP(self.host, self.user, self.password)
        except ftplib.all_errors as e:
            raise ShifterError(str(e))

    def path_exists(self, dst):
        d = os.path.dirname(dst)
        f = os.path.basename(dst)
        try:
            files = self.ftp.nlst(d)
        except ftplib.all_errors as e:
            raise ShifterError(str(e))
        # may be relative or absolute, so cope with both
        return (f in files) or (dst in files)

    def makedirs(self, dst):
        if self.path_exists(dst):
            pass
        else:
            dirname = os.path.dirname(dst)
            if dirname != '':
                self.makedirs(dirname)
            try:
                self.ftp.mkd(dst)
            except ftplib.all_errors as e:
                raise ShifterError(str(e))

    def uploadfile(self, src, dst):
        f = open(src, "r")
        try:
            self.ftp.storbinary("STOR " + dst, f)
        except ftplib.all_errors as e:
            raise ShifterError(str(e))
        f.close()

    def readlines(self, src):
        lines = []
        try:
            self.ftp.retrlines("RETR " + src, lambda line: lines.append(line))
        except ftplib.all_errors as e:
            raise ShifterError(str(e))
        return lines
        
    def removefile(self, dst):
        try:
            self.ftp.delete(dst)
        except ftplib.all_errors as e:
            raise ShifterError(str(e))

    def removedir_if_empty(self, dst):
        try:
            self.ftp.rmd(dst)
        except ftplib.error_perm:
            # wasn't empty, so ignore
            pass
        except ftplib.all_errors as e:
            raise ShifterError(str(e))

    def ls(self, dst):
        """Return directory listing, with relative paths."""
        try:
            maybe_abs_files = self.ftp.nlst(dst)
        except ftplib.all_errors as e:
            raise ShifterError(str(e))
        # may be relative or absolute, so cope with both
        return [ os.path.basename(x) for x in maybe_abs_files ]

    def close(self):
        try:
            self.ftp.quit()
        except ftplib.all_errors as e:
            raise ShifterError(str(e))

class SftpShifter(object):
    """Use SFTP to transfer files."""
    def __init__(self, host, user, port = 22):
        self.host = host
        self.user = user
        self.port = port

    def __str__(self):
        return "SftpShifter(host=" + self.host + ",user=" + self.user + ",port=" + str(self.port) + ")"

    def open(self):
        self.ssh_agent = paramiko.Agent()
        keys = self.ssh_agent.get_keys()
        if len(keys) != 1:
            raise ShifterError("Failed to get a private key from ssh-agent")
        try:
            self.transport = paramiko.Transport((self.host, self.port))
            self.transport.connect(username=self.user, pkey=keys[0])
            self.sftp_client = paramiko.SFTPClient.from_transport(self.transport)
        except paramiko.SSHException as e:
            raise ShifterError(str(e))

    def path_exists(self, dst):
        try:
            s = self.sftp_client.stat(dst)
            return True
        except (paramiko.SFTPError,IOError) as e:
            return False

    def makedirs(self, dst):
        if self.path_exists(dst):
            pass
        else:
            dirname = os.path.dirname(dst)
            if dirname != '':
                self.makedirs(dirname)
            try:
                self.sftp_client.mkdir(dst)
            except (paramiko.SFTPError,IOError) as e:
                raise ShifterError(str(e))

    def uploadfile(self, src, dst):
        try:
            self.sftp_client.put(src, dst)
        except (paramiko.SFTPError,IOError) as e:
            raise ShifterError(str(e))

    def readlines(self, src):
        lines = []
        try:
            f = self.sftp_client.open(src, 'r')
            for line in f:
                lines.append(line.rstrip('\n'))
            f.close()
        except (paramiko.SFTPError,IOError) as e:
            raise ShifterError(str(e))
        return lines

    def removefile(self, dst):
        try:
            self.sftp_client.remove(dst)
        except (paramiko.SFTPError,IOError) as e:
            raise ShifterError(str(e))

    def removedir_if_empty(self, dst):
        try:
            self.sftp_client.rmdir(dst)
        except (paramiko.SFTPError,IOError) as e:
            # wasn't empty, so ignore
            pass

    def ls(self, dst):
        """Return directory listing."""
        try:
            files = self.sftp_client.listdir(dst)
        except (paramiko.SFTPError,IOError) as e:
             raise ShifterError(str(e))
        return files

    def close(self):
        self.transport.close()
