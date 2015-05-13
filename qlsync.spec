Name:           qlsync
Version:        0.4
Release:        1%{?dist}
Summary:        Sync Quodlibet library to device.

License:        GPLv2
URL:            https://github.com/tesujimath/qlsync
Source0:        qlsync-%{version}.tgz

BuildRequires:  python2-devel
Requires:       pygobject2 pygtk2 quodlibet python-paramiko android-tools

%description
qlsync is a small GUI program for maintaining playlists and music
files on a portable device.  It uses Quodlibet to find playlists and
music files, but is otherwise independent.

Different transport protocols are supported to connect to your device:
filesystem (i.e. mounted mass storage devive), FTP, and SFTP.
MTP is not currently supported.

%define debug_package %{nil}

%prep
%setup -q

%build
%{__python2} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python2} setup.py install --skip-build --root %{buildroot}

%files
%doc LICENSE README.md README.iPod.md
%{_bindir}/*
%{python2_sitelib}/*

%changelog
* Sat May  9 2015 Simon Guest <simon.guest@tesujimath.org> 0.4-1
- first packaging
