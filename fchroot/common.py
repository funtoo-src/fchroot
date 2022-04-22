import argparse
import subprocess
import sys

RED = ""
GREEN = ""
CYAN = ""
END = ""

if sys.stdout.isatty():
    RED = '\033[31m'
    GREEN = '\033[32m'
    CYAN = '\033[36m'
    END = '\033[0m'


def die(msg):
    sys.stdout.write(msg + "\n")
    sys.exit(1)


def run_verbose(action, cmd_list):
    result = subprocess.run(cmd_list)
    action_out = (action + ":").ljust(6)
    if result.returncode == 0:
        if args.verbose:
            sys.stderr.write(GREEN + f"{' '.join(cmd_list)}" + END + "\n")
    else:
        sys.stderr.write(RED + "!!!" + END + f" {action_out}: {' '.join(cmd_list)}\n")
    return result.returncode


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("newroot", type=str)
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--preserve-env", action="store_true", default=False,
                    help="Preserve the current environment settings rather than wiping them by default.")
    ap.add_argument("--cpu", action="store", default=None, help="Specify specific CPU type for QEMU to use")
    return ap.parse_known_args()


args, commands = parse_args()
