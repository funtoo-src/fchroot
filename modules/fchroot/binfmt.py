#!/usr/bin/python3

import os, string, sys
from .qemu import qemu_arch_settings
from .exception import QEMUException, QEMUWrapperException

# Where our stuff will look for qemu binaries:
qemu_binary_path = "/usr/bin"

# Where our code will try to store our compiled qemu wrappers:
wrapper_storage_path = "/usr/share/fchroot/wrappers"

def native_arch_desc():
	uname_arch = os.uname()[4]
	if uname_arch in ["x86_64", "AMD64"]:
		host_arch = "x86-64bit"
	elif uname_arch in ["x86", "i686", "i386"]:
		host_arch = "x86-32bit"
	else:
		raise QEMUException("Arch of %s not recognized." % uname_arch)
	return host_arch


def supported_binfmts(native_arch_desc=None):
	if native_arch_desc is None:
		return set(qemu_arch_settings.keys())
	else:
		# TODO: return supported QEMU arch_descs specific to a native arch_desc.
		return set()


def get_binary_hexstring(path):
	chunk_as_hexstring = ""
	with open(path, 'rb') as f:
		for x in range(0, 19):
			chunk_as_hexstring += f.read(1).hex()
	return chunk_as_hexstring


def escape_hexstring(hexstring):
	to_process = hexstring
	to_output = ""
	while len(to_process):
		ascii_value = chr(int(to_process[:2], 16))
		to_process = to_process[2:]
		if ascii_value in set(string.printable):
			to_output += ascii_value
		else:
			to_output += "\\x" + "{0:02x}".format(ord(ascii_value))
	return to_output


def is_binfmt_registered(arch_desc):
	return os.path.exists("/proc/sys/fs/binfmt_misc/" + arch_desc)


def register_binfmt(arch_desc, wrapper_bin):
	if not os.path.exists(wrapper_bin):
		raise QEMUWrapperException("Error: wrapper binary %s not found.\n" % wrapper_bin)
	if arch_desc not in qemu_arch_settings:
		raise QEMUWrapperException("Error: arch %s not recognized. Specify one of: %s.\n" % (arch_desc, ", ".join(supported_binfmts())))
	if os.path.exists("/proc/sys/fs/binfmt_misc/%s" % arch_desc):
		raise QEMUWrapperException("Error: binary format %s already registered in /proc/sys/fs/binfmt_misc.\n" % arch_desc)
	try:
		with open("/proc/sys/fs/binfmt_misc/register", "w") as f:
			chunk_as_hexstring = qemu_arch_settings[arch_desc]['hexstring']
			mask_as_hexstring = "fffffffffffffffcfffffffffffffffffeffff"
			mask = int(mask_as_hexstring, 16)
			chunk = int(chunk_as_hexstring, 16)
			out_as_hexstring = hex(chunk & mask)[2:]
			f.write(":%s:M::" % arch_desc)
			f.write(escape_hexstring(out_as_hexstring))
			f.write(":")
			f.write(escape_hexstring(mask_as_hexstring))
			f.write(":/usr/local/bin/%s:\n" % os.path.basename(wrapper_bin))
	except (IOError, PermissionError) as e:
		raise QEMUWrapperException("Was unable to write to /proc/sys/fs/binfmt_misc/register.")