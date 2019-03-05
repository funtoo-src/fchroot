#!/usr/bin/python3

import os, string, sys
from .qemu import qemu_arch_settings

def get_binary_hexstring(path):
	chunk_as_hexstring = ""
	with open(path, 'rb') as f:
		for x in range(0, 19):
			chunk_as_hexstring += f.read(1).hex()
	return chunk_as_hexstring


printable_chars = set(string.printable)


def escape_hexstring(hexstring):
	global printable_chars
	to_process = hexstring
	to_output = ""
	while len(to_process):
		ascii_value = chr(int(to_process[:2], 16))
		to_process = to_process[2:]
		if ascii_value in printable_chars:
			to_output += ascii_value
		else:
			to_output += "\\x" + "{0:02x}".format(ord(ascii_value))
	return to_output


def configure_binfmt(arch_desc, wrapper_bin):
	if not os.path.exists(wrapper_bin):
		sys.stderr.write("Error: wrapper binary %s not found.\n" % wrapper_bin)
		sys.exit(1)
	if arch_desc not in qemu_arch_settings:
		sys.stderr.write("Error: arch %s not recognized. Specify one of: %s.\n" % (arch_desc, ", ".join(arch_dict.keys())))
		sys.exit(1)
	if os.path.exists("/proc/sys/fs/binfmt_misc/%s" % arch_desc):
		sys.stderr.write("Error: binary format %s already registered in /proc/sys/fs/binfmt_misc.\n" % arch_desc)
		sys.exit(1)
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