# fchroot

## Introduction

`fchroot`, also known as "Franken-Chroot" or "Funtoo Chroot", is a utility that helps
you to leverage the magic of QEMU to chroot into a non-native system. For example,
on your x86-compatible 64-bit PC, it is possible to chroot into a 32-bit or 64-bit
ARM environment and have it actually work. 

This is accomplished by leveraging the
"binfmt-misc" functionality built-in to the Linux kernel, combined with QEMU to
perform emulation of non-native instruction sets. `fchroot` itself doesn't do any
magic except provide a very easy-to-use mechanism to get this to work, typically
requiring little or no manual configuration. You simply run `fchroot` just like
`chroot`, and everything works. Well, I suppose that is a bit magical :) Here's an
example of how things work with fchroot. Let's say you are on your 64-bit x86-64
PC, and want to enter a 64-bit ARM environment. Do this:

```bash
my64bitpc # tar xpvf stage3-arm64bit.tar.xz
my64bitpc # fchroot arm64-root
>>> arm-64bit frankenchroot B]...
#
```

That last `#` prompt may not look like anything special, but you are now inside a
64-bit ARM frankenchroot. A 64-bit ARM shell is providing that prompt to you, and
if you run a standard Linux command, it will be running the 64-bit ARM variant of
that command using QEMU emulation. Pretty cool stuff.

## What `fchroot` Does For You

The `fchroot` command does lots of things automatically for you to make your 
franken-chroot experience as seamless as possible. First, note that `fchroot` is
designed to have a similar calling convention to the standard Linux `chroot` command --
in fact, at the very end of doing all its magic, it passes all of its arguments to
`chroot` to get you inside the frankenchroot. But `fchroot` does quite a bit of
grunt-work to make the `chroot` work:

* `fchroot` will look inside the specified directory and attempt to auto-detect
what kind of non-native environment it's dealing with. It will currently recognize arm-32bit
and arm-64bit environments.
* `fchroot` will check to see if QEMU is available for the detected non-native
architecture and abort with a (hopefully) useful error message if it is not.
* `fchroot` will use `gcc` to compile a special wrapper that will be used inside
the chrooted environment, and store it in `/usr/share/fchroot/wrappers` so it is
available for later use.
* `fchroot` will leverage Linux's `binfmt_misc` functionality and register a handler
so that the kernel will know to use our wrapper (and QEMU) to run non-native binaries.
* `fchroot` will copy the necessary QEMU binary as well as its wrapper into 
`/usr/local/bin/` inside the chrooted environment.
* `fchroot` will mount `/proc`, `/dev` (bind-mount) and `/sys` (bind-mount) within the
chroot environment automatically if they are not already mounted.
* `fchroot` will copy the local system's `/etc/resolv.conf` to the chroot environment
so that DNS resolution will work properly.
* `fchroot` will then `execvp` the `chroot` command to place you inside the franken-chroot
environment.

## Prerequisites

This section lists the prerequisites for getting `fchroot` running -- in other words,
the things that *you* are responsible for ensuring are done. `fchroot` takes care
of the rest.

### Host and Emulated System

``fchroot`` has been used on x86-compatible 64-bit systems, and currently supports
arm-32bit and arm-64bit chrooted environments. It is relatively easy to add support
for new native and emulated systems -- the code is designed to accept patches for
new architectures -- but for now, be aware of the current architectures supported.

### QEMU

QEMU will need to be installed with the ``aarch64`` and ``arm`` user targets enabled.
In addition, it will need to be compiled as a *static* binary. In Funtoo Linux and
Gentoo Linux, this can be accomplished by adding the following configuration
prior to running ``emerge qemu``:

Add to ``/etc/make.conf``:

```bash
QEMU_USER_TARGETS="aarch64 arm"
```

Add to ``/etc/portage/package.use``:

```bash
app-emulation/qemu static-user
dev-libs/glib static-libs
sys-apps/attr static-libs
sys-libs/zlib static-libs
dev-libs/libpcre static-libs
```

### binfmt_misc

In addition, you will need to ensure that ``binfmt_misc`` functionality is enabled
in-kernel or as a module. By default, this is the case when using Funtoo Linux with
its default ``debian-sources-lts`` kernel.

## Setup

The easiest way to set up `fchroot` is to clone it directly from https://code.funtoo.org:

```bash
# git clone https://code.funtoo.org/bitbucket/scm/~drobbins/fchroot.git
```

You can then simply run ``fchroot`` directly from the git repository:

```bash
# fchroot/bin/fchroot /path/to/chroot
```

## Acknowledgements

The `fchroot` command automates a process that was documented at the following locations:

* https://wiki.gentoo.org/wiki/Embedded_Handbook/General/Compiling_with_qemu_user_chroot
* https://github.com/sakaki-/gentoo-on-rpi3-64bit/wiki/Build-aarch64-Packages-on-your-PC%2C-with-User-Mode-QEMU-and-binfmt_misc

Many thanks to Sakaki and others who documented this process.

## Contributing

To contribute, please visit https://code.funtoo.org/bitbucket/users/drobbins/repos/fchroot/browse and submit a pull request.
For more information on how to submit pull requests on code.funtoo.org, see the following YouTube video: https://www.youtube.com/watch?v=V6PfB64oMWo

## Author and Copyright

Copyright 2020 Daniel Robbins, Funtoo Solutions, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
