# KPC101 standalone control

microTool includes a compact live control below Exposure. Use Find, select the
serial, Connect, then Enable. The linked slider and numeric input send live
voltage targets in open loop, or percent-of-travel targets in closed loop.
Slider targets are coalesced at a 50 ms UI interval, with only one hardware
operation in flight, keeping camera acquisition responsive. Numeric input
applies on Enter or when focus leaves the field. Connection preserves the
device mode and output state; quitting disconnects without changing output.

Reusable control for the Thorlabs K-Cube Piezo Controller and Strain Gauge
Reader (KPC101, device type 113). This folder is self-contained and does not
change microTool's main UI or require its camera dependencies.

## Start the test app

From the microTool repository root:

```powershell
python -m pip install -r instruments/KPC101/requirements.txt
python -m instruments.KPC101.test_app --simulate
python -m instruments.KPC101.test_app
```

Or from this folder: `python test_app.py --simulate`.
Simulation is an in-memory functional demo, not a model of piezo dynamics.

Hardware requires Windows, Thorlabs Kinesis with USB drivers, and matching
Python/Kinesis architecture (normally 64-bit). The default install location is
`C:\Program Files\Thorlabs\Kinesis`. Override it using `--kinesis-path` or the
`THORLABS_KINESIS_PATH` environment variable. No Python.NET is needed.
Vendor DLLs remain in the installed Kinesis directory and are not bundled here.

Configure the connected actuator and its calibration/voltage limit in Kinesis
first, then close Kinesis and other apps using the device. Power and connect
the KPC101, select **Find devices**, then **Connect**. Connection loads saved
settings and starts polling; it does not enable output, zero, or change mode.
Use **Enable output**, choose and apply the mode, and explicitly set a target.
Voltage targets are nonnegative and limited to the configured maximum.
Position targets are 0–100% of configured travel and require closed-loop mode
with strain-gauge feedback. Both smoothed modes are supported.

**Zero reference** starts the device's reference calibration; this can move the
actuator and usually takes about 10 seconds. Monitor zeroing/zeroed readback.
**Disable output** explicitly disables the channel. Disconnect/closing the app
leaves the output state unchanged; it is not a stop or zero-voltage command.
Readback is cached by Kinesis polling and does not guarantee a settled position.
Existing external-input and potentiometer settings are preserved; those inputs
can also contribute to output. Configure software-only input in Kinesis when
you want software targets to be the sole control source.

## Later integration

The controller has no Qt dependency and loads the DLL only when hardware is
used. Its public methods are thread-safe and raise `KPCError` for device/state
errors and `ValueError` for invalid targets. Calls can block briefly, so use a
worker when integrating into a GUI.

```python
from instruments.KPC101 import KPC101, Mode

piezo = KPC101()  # simulate=True for hardware-free development
serials = piezo.discover()
if not serials:
    raise RuntimeError("No KPC101 found")
try:
    piezo.connect(serials[0])
    print(piezo.status())
    # Explicit enable/mode/target commands belong in the application's workflow.
finally:
    piezo.disconnect()
```

To embed the same UI:

```python
from instruments.KPC101.panel import KPC101Panel
panel = KPC101Panel(parent=host_widget)
host_layout.addWidget(panel)
# Call panel.shutdown() from the host's close/removal handler.
```

The panel serializes all device operations in one worker thread and updates
Qt widgets on the GUI thread. Do not control the same device from another
panel/process concurrently. `shutdown()` finishes queued work and disconnects.

## Verification

```powershell
python -m unittest instruments.KPC101.test_controller -v
```

Tests cover command guards, invalid targets, reference-zero state, connection
cleanup, and native voltage/position scaling. Hardware behavior still needs
validation with the actual controller and actuator.

API references: the installed
`Thorlabs.MotionControl.KCube.PiezoStrainGauge.h` is the source for C signatures,
status bits and units; see also
[Thorlabs' KPC101 example](https://github.com/Thorlabs/Motion_Control_Examples/blob/main/Python/Kinesis/KCube/KPC101/KPC101_pythonnet.py)
and [motion control examples](https://github.com/Thorlabs/Motion_Control_Examples).
