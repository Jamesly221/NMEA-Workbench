# Reference sources and interpretation

The initial reference entries use original summaries informed by Trimble's published OEM GNSS documentation:

- RMC: https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-rmc.html
- GGA: https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-gga.html
- VTG: https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-vtg.html
- HDT: https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-hdt.html

These sources describe manufacturer implementations; they do not cover every NMEA revision or instrument. Optional fields remain visible, and unsupported data is not silently discarded. The HEHDT sample is generated for this tool; a talker identifier identifies the data source, not the sentence structure.

All bundled sample checksums are computed from their sentence bodies. The demo deliberately changes one checksum, omits one checksum, and includes invalid values and text.

Checksum computation uses XOR over the ASCII characters between the starting delimiter and `*`. A checksum match is a transport-integrity check, independent of a receiver's validity status. RMC status V, GGA quality 0 and a mode indicating invalid data are reported for review. Empty optional values are preserved; this release does not certify full standards compliance.

Packaging documentation: https://pyinstaller.org/en/stable/
Desktop widgets: https://docs.python.org/3/library/tkinter.ttk.html
