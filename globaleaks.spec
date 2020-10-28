%global commit      5762d913f9b80a4f30d41cc0ee9b1ee41242b500
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global version     4.0.58

%define debug_package %{nil}
%define _unpackaged_files_terminate_build 0

Name: globaleaks
Version: %{version}
Release: 1.%{shortcommit}%{?dist}
Summary: Opensource whistleblowing platform.
License: see /usr/share/doc/globaleaks/copyright
Group: Converted/web
ExclusiveArch: x86_64

URL:            https://globaleaks.org
Source0:        https://github.com/globaleaks/GlobaLeaks/archive/%{commit}.tar.gz

BuildRequires: nodejs
BuildRequires: python36

%prep
%setup -n globaleaks-%{version}

# Build Client
cd client
npm install -d
./node_modules/grunt/bin/grunt copy:sources
cd ../

# Build Backend
cd backend
python3 setup.py build
cd ../

%install

# Install Backend
cd backend
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
cd ../

# Install Rest
mkdir -p $RPM_BUILD_ROOT/usr/share/globaleaks/client
cp LICENSE $RPM_BUILD_ROOT/usr/share/globaleaks/LICENSE
cp CHANGELOG $RPM_BUILD_ROOT/usr/share/globaleaks/CHANGELOG
cp backend/default $RPM_BUILD_ROOT/usr/share/globaleaks/default
cp client/build/* $RPM_BUILD_ROOT/usr/share/globaleaks/client

%pre
#!/bin/sh
# This is the post installation script for globaleaks
set -e



if [ "$1" = "upgrade" ]; then
  systemctl stop globaleaks || true
fi

if [ ! -z "$(ls -A /var/globaleaks 2>/dev/null)" ]; then
  if ! id -u globaleaks >/dev/null 2>&1; then
    adduser --quiet \
            --system \
            --home /var/globaleaks \
            --shell /bin/false \
            globaleaks
  fi
fi


%post
#!/bin/sh
# This is the post installation script for globaleaks
set -e

DISTRO="unknown"
DISTRO_CODENAME="unknown"
if which lsb_release >/dev/null; then
  DISTRO="$(lsb_release -is)"
  DISTRO_CODENAME="$(lsb_release -cs)"
fi

if [ "$DISTRO" = "LinuxMint" ]; then
  DISTRO="Ubuntu"
  DISTRO_CODENAME=`grep UBUNTU_CODENAME /etc/os-release | sed -e 's/UBUNTU_CODENAME=//'`
fi

# Create globaleaks user and add the user to required groups
if ! id -u globaleaks >/dev/null 2>&1; then
  adduser --quiet \
          --system \
          --home /var/globaleaks \
          --shell /bin/false \
          globaleaks
fi

usermod -a -G toranon globaleaks

# Create globaleaks service directories with proper permissios
gl-fix-permissions

# Remove old configuration of Tor used before txtorcon adoption
if $(grep -q -i globaleaks /etc/tor/torrc >/dev/null 2>&1); then
  sed -i '/BEGIN GlobaLeaks/,/END GlobaLeaks/d' /etc/tor/torrc
  systemctl restart tor
fi

# raise haveged default water mark to 4067 bits
# for the reason for the 4067 bits see:
#   - https://github.icom/globaleaks/GlobaLeaks/issues/1722
cp /usr/lib/systemd/system/haveged.service /etc/systemd/system/haveged.service
sed -i 's/-w 1024/-w 4067/g' /etc/systemd/system/haveged.service
systemctl restart haveged

%preun
#!/bin/sh
set -e

systemctl stop globaleaks

%description
GlobaLeaks is an open source project aimed to create a worldwide, anonymous,
censorship-resistant, distributed whistleblowing platform.

%files
/usr/bin/gl-admin
/usr/bin/gl-fix-permissions
/usr/bin/globaleaks
/usr/lib/python3.6/dist-packages/globaleaks/
/usr/lib/python3.6/dist-packages/globaleaks-4.0.58.egg-info/
/usr/share/doc/globaleaks/
/usr/share/globaleaks/
