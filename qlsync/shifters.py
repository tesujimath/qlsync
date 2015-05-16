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
import subprocess

# decimal not binary for disk drives and FLASH memory,
# see http://en.wikipedia.org/wiki/Gigabyte
KILO = 1000
MEGA = KILO * KILO
GIGA = MEGA * KILO

def parse_as_gigabytes(s):
    try:
        x = float(s[:-1])
        if s[-1].lower() == 'g':
            gigabytes = x
        elif s[-1].lower() == 'm':
            gigabytes = x * 1.0 / KILO
        elif s[-1].lower() == 'k':
            gigabytes = x * 1.0 / MEGA
        else:
            gigabytes = None
    except:
        gigabytes = None
    return gigabytes

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

    def get_storage_space(self, dst):
        """Disk space (avail, total) in GB."""
        try:
            s = os.statvfs(dst)
            avail = s.f_bsize * s.f_bavail * 1.0 / GIGA
            total = s.f_bsize * s.f_blocks * 1.0 / GIGA
        except:
            avail = None
            total = None
        return (avail, total)

    def flush(self):
        # ensure everything is on the disk
        os.system("sync")

    def close(self):
        pass

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

    def get_storage_space(self, dst):
        """Disk space (avail, total) in GB."""
        return (None, None)             # unknown

    def flush(self):
        pass

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

    def get_storage_space(self, dst):
        """Disk space (avail, total) in GB."""
        return (None, None)             # unknown

    def flush(self):
        pass

    def close(self):
        self.transport.close()

def quote(x):
    if " " in x:
        return "'%s'" % x
    else:
        return x

def quote_all(xs):
    return [quote(x) for x in xs]

def adb(commands, serial = None):
    """Run adb command for given device, return (rc, stdout, stderr)."""
    if serial:
        command_prefix = ["adb", "-s", serial]
    else:
        command_prefix = ["adb"]
    print("%s" % ' '.join(command_prefix + commands))
    try:
        adb = subprocess.Popen(command_prefix + commands, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        adb.wait()
        stdout_lines = [line.rstrip('\r\n') for line in adb.stdout.readlines()]
        stderr_lines = [line.rstrip('\r\n') for line in adb.stderr.readlines()]
        print("%s\n%s" % ('\n'.join(stdout_lines), '\n'.join(stdout_lines)))
        return (adb.returncode, stdout_lines, stderr_lines)
    except OSError as e:
        raise ShifterError("adb %s" % str(e))

class AdbShifter(object):
    """Use ADB to transfer files."""
    def __init__(self, sdcardroot, serial):
        print("AdbShifter::__init__(%s, %s)" % (sdcardroot, serial))
        self.sdcardroot = sdcardroot
        self.serial = serial

    def __str__(self):
        return "AdbShifter(serial=" + self.serial + ")"

    def adb(self, commands):
        return adb(commands, self.serial)

    def open(self):
        """Confirm the device is there."""
        print("AdbShifter::open()")
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "echo"])
        if rc != 0:
            raise ShifterError(", ".join(stderr_lines))

    def path_exists(self, dst):
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "ls", "-d", dst])
        return rc == 0 and stdout_lines and stdout_lines[0] == dst

    def makedirs(self, dst):
        if self.path_exists(dst):
            pass
        else:
            (rc, stdout_lines, stderr_lines) = self.adb(["shell", "mkdir", "-p", dst])
            if rc != 0:
                raise ShifterError(", ".join(stderr_lines))

    def uploadfile(self, src, dst):
        (rc, stdout_lines, stderr_lines) = self.adb(["push", src, dst])
        if rc != 0:
            raise ShifterError(", ".join(stderr_lines))

    def readlines(self, dst):
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "cat", dst])
        if rc != 0:
            raise ShifterError(", ".join(stderr_lines))
        print("readlines %s\n%s" % (dst, '\n'.join(stdout_lines)))
        return stdout_lines

    def removefile(self, dst):
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "rm", dst])
        if rc != 0:
            raise ShifterError(", ".join(stderr_lines))

    def removedir_if_empty(self, dst):
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "rmdir", dst])
        # ignore all errors, since this fails if not empty and we don't care

    def ls(self, dst):
        """Return directory listing."""
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "ls", dst])
        if rc != 0:
            raise ShifterError(", ".join(stderr_lines))
        print("ls %s\n%s" % (dst, '\n'.join(stdout_lines)))
        return stdout_lines

    def get_storage_space(self, dst):
        """Disk space (avail, total) in GB."""
        # Example Android df output:
        # Filesystem             Size   Used   Free   Blksize
        # /storage/sdcard0         9G     4G     5G   65536
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "df", dst])
        if rc == 0 and len(stdout_lines) >= 2:
            fields = stdout_lines[1].split()
            return (parse_as_gigabytes(fields[3]), parse_as_gigabytes(fields[1]))
        else:
            return (None, None)

    def flush(self):
        """Trigger a rescan of the sdcard."""
        print("AdbShifter::flush()")
        (rc, stdout_lines, stderr_lines) = self.adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_MOUNTED", "-d", "file://%s" % self.sdcardroot])
        if rc != 0:
            raise ShifterError(", ".join(stderr_lines))

    def close(self):
        print("AdbShifter::close()")
        pass
