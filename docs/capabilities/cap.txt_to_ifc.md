# Capability: Text to IFC (v0)

ID: cap.txt_to_ifc
Status: demo

## Purpose
Convert minimal natural language or structured text room specifications into Industry Foundation Classes (IFC) 3D models.

## v0 Implementation
- **Inputs**: `.txt` file with `ROOM name=... width=... depth=... height=...`
- **Outputs**: 
  - `{RoomName}.ifc`: Standardized BIM exchange file (minimal entities).
  - `manifest.json`: Cryptographic hashes for output integrity.
  - `receipt_{id}.json`: Formal run receipt conforming to ORCA schemas.

## Verification
- Run: `python tools/verify_txt_to_ifc_m14.py`

## Schemas
- Uses: `orca.capability.run_receipt@0.1.schema.json`
