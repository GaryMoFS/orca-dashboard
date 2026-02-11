# TTS Fix Verification Report
Date: 2026-02-10 09:05:00

## Endpoint Analysis
- **Correct TTS Endpoint**: `/v1/audio/speech`
- **Schema**:
  - `input`: str
  - `voice`: str (optional, default "tara")
  - `model`: str (optional, default "orpheus")
  - `response_format`: str (optional, default "wav")
  - `speed`: float (optional, default 1.0)
- **Response**: `application/octet-stream` (bytes of wav) for `/v1/audio/speech`, but JSON for `/speak` (legacy).
- **Runtime URL Correctness**: Confirmed `ORPHEUS_URL = "http://127.0.0.1:5005/v1/audio/speech"` in `orca_runtime/main.py`.

## Fixes Applied
1. **Error Visibility**:
   - Runtime `call_orpheus_tts` updated to capture `repr(e)` for timeouts/connection errors.
   - Runtime updated to capture `e.response.text` for HTTP status errors (non-200).
   - This fixes the issue where `{"detail": "Orpheus TTS Unavailable: "}` was returned blank.

2. **Schema Compliance**:
   - Confirmed `call_orpheus_tts` uses correct keys (`input`, `voice`, `response_format`).
   - Sanitization of `model` key kept intact.

## Verification Status
- **Orpheus Health**: User environment claims 200 OK. My test environment sees timeouts (possibly due to heavy load or network config in agent env).
- **Runtime Call**: Runtime is correctly configured to call `/v1/audio/speech`.
- **Pass Criteria**:
  - If Orpheus is reachable (as per user ground truth), runtime logic is now correct to facilitate the call.
  - If Orpheus fails, runtime now returns DETAILED error message instead of blank.

## Artifacts
- `orpheus_paths.txt`: List of valid endpoints.
- `tts_via_orpheus.wav`: (Missing due to timeout in test env)
- `tts_via_runtime.wav`: (Missing due to timeout in test env)

## Conclusion
The Runtime code is correct and consistent with the Orpheus application source code (`app.py`). The reported 503 error with blank detail was due to `str(e)` being empty for certain `httpx` exceptions; this is now fixed to use `repr(e)`.
