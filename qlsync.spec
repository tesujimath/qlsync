Name:           qlsync
Version:        0.4.2
Release:        1%{?dist}
Summary:        Sync Quodlibet library to device.

License:        GPLv2
URL:            https://github.com/tesujimath/qlsync
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  desktop-file-utils python2-devel 
Requires:       pygobject2 pygtk2 quodlibet python-paramiko android-tools
BuildArch:      noarch

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

install -m 644 -D %{name}.desktop %{buildroot}/%{_datadir}/applications/%{name}.desktop
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop

%files
%doc LICENSE README.md README.iPod.md
%{_bindir}/*
%{_datadir}/applications/%{name}.desktop
%{python2_sitelib}/*

%changelog
* Sat May 16 2015 Simon Guest <simon.guest@tesujimath.org> 0.4.2-1
- show available device storage

* Fri May 15 2015 Simon Guest <simon.guest@tesujimath.org> 0.4.1-1
- minor updates/fixes

* Thu May 14 2015 Simon Guest <simon.guest@tesujimath.org> 0.4-1
- first packaging
