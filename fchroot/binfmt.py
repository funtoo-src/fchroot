#!/usr/bin/env python3

import string

from fchroot.common import *


class QEMUException(Exception):
	pass


class QEMUWrapperException(QEMUException):
	pass


qemu_arch_settings = {
	'riscv-64bit': {
		'qemu_binary': 'qemu-riscv64',
		'qemu_cpu': 'sifive-u54',
		'elf': {
			'magic': '7f454c460201010000000000000000000200f300',
			'mask': 'ffffffffffffff00fffffffffffffffffeffffff',
		},
	},
	'arm-64bit': {
		'qemu_binary': 'qemu-aarch64',
		'qemu_cpu': 'cortex-a72',
		'elf': {
			'magic': '7f454c460201010000000000000000000200b700',
			'mask': 'ffffffffffffff00fffffffffffffffffeffffff',
		},
	},
	'arm-32bit': {
		'qemu_binary': 'qemu-arm',
		'qemu_cpu': 'cortex-a7',
		'elf': {
			'magic': '7f454c4601010100000000000000000002002800',
			'mask': 'ffffffffffffff00fffffffffffffffffeffffff',
		},
	},
	'powerpc-64bit': {
		'qemu_binary': 'qemu-ppc64',
		'qemu_cpu': 'power7',
		'elf': {
			'magic': '7f454c4602020100000000000000000000020015',
			'mask': 'ffffffffffffff00fffffffffffffffffffeffff',
		},
	},
	'powerpc-32bit': {
		'qemu_binary': 'qemu-ppc',
		'qemu_cpu': 'max',
		'elf': {
			'magic': '7f454c4601020100000000000000000000020014',
			'mask': 'ffffffffffffff00fffffffffffffffffffeffff',
		},
	},
	'x86-64bit': {
		'qemu-binary': 'qemu-x86_64',
		'qemu_cpu': 'max',
		'elf': {
			'magic': '7f454c4602010100000000000000000002003e',
			'mask': 'ffffffffffffff00fffffffffffffffffffeffff',
		},
	},
	'x86-32bit': {
		'qemu-binary': 'qemu-i386',
		'qemu_cpu': 'max',
		'elf': {
			'magic': '7f454c46010101000000000000000000020003',
			'mask': 'ffffffffffffff00fffffffffffffffffffeffff',
		},
		'native-support': ['x86-64bit']
	}
}


def compile_wrapper(qemu_arch, out_path, qemu_cpu=None):
	"""
	Compiles a QEMU wrapper using gcc. Will raise QEMUWrapperException if any error is encountered along the way.
	:param qemu_arch: arch to build for -- should be 'arm-64bit' or 'arm-32bit' at the moment.
	:return: None
	"""
	wrapper_code = """#include <string.h>
#include <unistd.h>

int main(int argc, char **argv, char **envp) {{
	char *newargv[argc + 3];

	newargv[0] = argv[0];
	newargv[1] = "-cpu";
	newargv[2] = "{qemu_cpu}";

	memcpy(&newargv[3], &argv[1], sizeof(*argv) * (argc -1));
	newargv[argc + 2] = NULL;
	return execve("/usr/local/bin/{qemu_binary}", newargv, envp);
}}
	"""

	qemu_binary = qemu_arch_settings[qemu_arch]["qemu_binary"]
	qemu_cpu = qemu_cpu if qemu_cpu is not None else qemu_arch_settings[qemu_arch]["qemu_cpu"]

	with open(os.path.join(out_path, "qemu-%s-wrapper.c" % qemu_arch), "w") as f:
		f.write(wrapper_code.format(qemu_binary=qemu_binary, qemu_cpu=qemu_cpu))
	success = run_verbose("wrapper",
	                      ["gcc", "-static", "-O2", "-s", "-o",
	                       f"{out_path}/qemu-{qemu_arch}-wrapper",
	                       f"{out_path}/qemu-{qemu_arch}-wrapper.c"]
	                      )
	if not success:
		raise QEMUWrapperException("Compilation failed.")


# Where our stuff will look for qemu binaries:
qemu_binary_path = "/usr/bin"


def native_arch_desc():
	uname_arch = os.uname()[4]
	if uname_arch in ["x86_64", "AMD64"]:
		host_arch = "x86-64bit"
	elif uname_arch in ["x86", "i686", "i386"]:
		host_arch = "x86-32bit"
	else:
		raise QEMUException("Arch of %s not recognized." % uname_arch)
	return host_arch


def qemu_path(arch_desc):
	return os.path.join(qemu_binary_path, qemu_arch_settings[arch_desc]['qemu_binary'].lstrip("/"))


def qemu_exists(arch_desc):
	return os.path.exists(qemu_path(arch_desc))


def supported_binfmts(native_arch_desc=None):
	if native_arch_desc is None:
		return set(qemu_arch_settings.keys())
	else:
		# TODO: return supported QEMU arch_descs specific to a native arch_desc.
		return set()


def get_arch_of_binary(path):
	found = get_binary_hexstring(path)
	logging.debug(f"Discovered hexstring: {found} for {path}")
	for arch_desc, arch_settings in qemu_arch_settings.items():
		magic = arch_settings["elf"]["magic"]
		mask = arch_settings["elf"]["mask"]
		magic_int = int(magic, 16)
		mask_int = int(mask, 16)
		found_int = int(found[0:len(magic)], 16)
		if magic_int & mask_int == found_int & mask_int:
			logging.debug(f"Found {arch_desc}")
			return arch_desc
		else:
			logging.debug(f"Root is NOT {arch_desc} as {found} does not match {magic}")
	return None


def get_binary_hexstring(path):
	chunk_as_hexstring = ""
	with open(path, 'rb') as f:
		for x in range(0, 23):
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
		sys.stderr.write("Warning: binary format %s already registered in /proc/sys/fs/binfmt_misc.\n" % arch_desc)
	try:
		with open("/proc/sys/fs/binfmt_misc/register", "w") as f:
			magic = int(qemu_arch_settings[arch_desc]["elf"]["magic"], 16)
			mask_as_hexstring = qemu_arch_settings[arch_desc]["elf"]["mask"]
			mask = int(mask_as_hexstring, 16)
			out_as_hexstring = hex(magic & mask)[2:]  # This strips the "0x"
			f.write(f":{arch_desc}:M::{escape_hexstring(out_as_hexstring)}:{escape_hexstring(mask_as_hexstring)}:/usr/local/bin/{os.path.basename(wrapper_bin)}:C\n")
	except (IOError, PermissionError) as e:
		raise QEMUWrapperException("Was unable to write to /proc/sys/fs/binfmt_misc/register.")


def setup_wrapper(chroot_path, arch_desc):
	# ensure required qemu binary exists in /usr/bin on host:
	if not qemu_exists(arch_desc):
		die(f"Couldn't find qemu binary at {qemu_path(arch_desc)} Exiting.")

	# create /usr/local/bin in chroot if it doesn't exist:
	local_bin_path = os.path.join(chroot_path, "usr/local/bin")
	if not os.path.exists(local_bin_path):
		os.makedirs(local_bin_path)

	# copy static qemu binary into chroot from host:
	chroot_qemu_path = os.path.join(chroot_path, "usr/local/bin/", qemu_arch_settings[arch_desc]["qemu_binary"])
	if not os.path.exists(chroot_qemu_path):
		result = subprocess.run(["/bin/cp", qemu_path(arch_desc), chroot_qemu_path])
		if result.returncode != 0:
			die("Unable to copy qemu into chroot. Exiting.")

	# create C wrapper, and compile it. Both will end up in /usr/local/bin inside chroot:
	chroot_wrapper_path = os.path.join(chroot_path, "usr/local/bin")
	os.makedirs(chroot_wrapper_path, exist_ok=True)
	compile_wrapper(arch_desc, chroot_wrapper_path, qemu_cpu=args.cpu)

	# register binary format if it is not yet registered:
	if not is_binfmt_registered(arch_desc):
		register_binfmt(arch_desc, chroot_qemu_path)

# vim: ts=4 sw=4 noet
