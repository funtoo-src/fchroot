#!/usr/bin/python3

import os
from .binfmt import wrapper_storage_path, qemu_binary_path
from .exception import QEMUWrapperException


qemu_arch_settings = {
	'arm-64bit': {
		'qemu_binary': 'qemu-aarch64',
		'qemu_cpu': 'cortex-a53',
		'hexstring': '7f454c460201010000000000000000000200b7',
	},
	'arm-32bit': {
		'qemu_binary': 'qemu-arm',
		'qemu_cpu': 'cortex-a7',
		'hexstring': '7f454c46010101000000000000000000020028',
	}
}

native_support = {
	'x86-64bit': ['x86-32bit'],
	'x86-32bit': [],
	'arm-64bit': ['arm-32bit'],
	'arm-32bit': []
}


def compile_wrapper(qemu_arch):
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
	qemu_wrapper_binary = "%s/%s" % (qemu_binary_path, qemu_arch_settings[qemu_arch]['qemu_binary'])

	if not os.path.exists(qemu_wrapper_binary):
		raise QEMUWrapperException("Please ensure that %s exists first." % qemu_wrapper_binary)
	try:
		with open(os.path.join(wrapper_storage_path, "qemu-%s-wrapper.c" % qemu_arch), "w") as f:
			f.write(wrapper_code.format(**qemu_arch_settings[qemu_arch]))
		retval = os.system("cd {wrapper_path}; gcc -static -O2 -s -o qemu-{qemu_arch}-wrapper qemu-{qemu_arch}-wrapper.c".format(wrapper_path=wrapper_storage_path, qemu_arch=qemu_arch))
		if retval != 0:
			raise QEMUWrapperException("Compilation failed.")
	except (IOError, PermissionError) as e:
		raise QEMUWrapperException(str(e))
