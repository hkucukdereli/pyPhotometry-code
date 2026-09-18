# Diagnostic script for problems connecting to boards or the GUI hanging at startup. Lists the
# serial ports on the computer, probes each port that the GUI would treat as a possible pyboard,
# and reports how long each probe took. If anything hangs, the Python stack of every thread
# is printed every 15 seconds showing where it is stuck.
#
# Usage (from the pyPhotometry directory):
#     python tools/check_serial_ports.py         # List and probe serial ports.
#     python tools/check_serial_ports.py --gui   # Then also launch the GUI with the hang watchdog.

import sys
import time
import platform
import faulthandler
from pathlib import Path

# Add pyPhotometry directory to sys.path so GUI modules can be imported.
pyphotometry_dir = str(Path(__file__).parents[1])
sys.path.append(pyphotometry_dir)

import serial
from serial.tools import list_ports

faulthandler.enable()
faulthandler.dump_traceback_later(15, repeat=True)  # Print stack of all threads every 15s while hung.

print(f"Python {platform.python_version()} on {platform.platform()}, pyserial {serial.__version__}\n")

from GUI.acquisition_board import get_board_info, is_pyboard_port  # noqa: E402

# List serial ports, flagging those the GUI probes as possible pyboards.
ports = sorted(list_ports.comports(), key=lambda c: c.device)
print("Serial ports:")
for c in ports:
    probed = is_pyboard_port(c)
    print(f"  {c.device:8s} {'[probed by GUI]' if probed else '[ignored by GUI]':17s} {c.description}  ({c.hwid})")
if not ports:
    print("  none found")
print()

# Probe each candidate port, timing each step.
for c in ports:
    if is_pyboard_port(c):
        print(f"Probing {c.device} ...", flush=True)
        start_time = time.time()
        unique_id, flashdrive_enabled = get_board_info(c.device)
        elapsed = time.time() - start_time
        if unique_id is None:
            print(f"  no response as a pyboard after {elapsed:.1f}s\n", flush=True)
        else:
            print(f"  pyboard with unique ID {unique_id}, flashdrive {'on' if flashdrive_enabled else 'off'}, "
                  f"in {elapsed:.1f}s\n", flush=True)

if "--gui" in sys.argv:
    print("Launching GUI with hang watchdog ...", flush=True)
    from GUI.GUI_main import launch_GUI

    launch_GUI()
else:
    faulthandler.cancel_dump_traceback_later()
    print("Done. Run with --gui to also launch the GUI with the hang watchdog.")
