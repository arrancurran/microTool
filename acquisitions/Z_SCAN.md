# Z scan

In Acquisition Settings, **Time Series** holds the existing mode, frame rate,
frame count and estimates. **Z Scan** holds start/end/increment and settle time.
Directory and experiment name below the tabs apply to both acquisition types.

Connect and enable the KPC101 before starting a scan. Z values use the current
piezo mode: volts in open loop, percent of calibrated travel in closed loop.
These are not micrometres. Use a positive increment for either direction; both
endpoints are included, with a shorter last step if needed. Equal endpoints
capture one image. The piezo stays at the last commanded position when done.

Each plane moves, waits for the selected settle time (minimum 0.3 s), checks
readback, starts camera acquisition, captures a fresh image and stops camera
acquisition before the next move. Readback must be within 0.1% travel in closed
loop, or 0.02 V / two device units in open loop; otherwise acquisition times out
after five seconds. Open-loop voltage readback does not measure physical Z.
Choose settle time for your actuator/sample; there is no physical settling
guarantee from voltage readback alone.

Live view pauses during scans and resumes afterwards if it was running. Manual
piezo, camera exposure/ROI controls and competing acquisition actions are locked
during the scan. **Stop Scan** keeps completed planes. Shutdown stops the scan
before disconnecting camera/piezo. A camera API call already in progress must
return before stopping can finish.

Output: `<experiment>_zscan_<timestamp>.h5`, exclusively created, containing:

- `frames`: image stack `(plane, height, width)`.
- `z_positions`: commanded Z aligned with saved frames, with a `units` attribute.
- `z_readback`: readback immediately before capture, in the same units.
- `z_requested`: full planned Z sequence, including uncaptured planes if stopped.
- `timestamps`: host capture timestamps, in Unix seconds.
- `optical traps`: SLM spot settings at scan start.

File attributes include piezo serial/mode, exposure/ROI metadata, settle time,
requested/acquired counts, start/end times, and `Scan Status` (`complete`,
`cancelled`, or `failed`). Completed planes are flushed individually and kept
on cancellation or failure; failed files include an error message.

Tests: `python -m unittest discover -s tests -p test_z_scan.py -v`.
