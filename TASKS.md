# ORCA Dashboard Tasks

## Agents & Feature Branches
1. **Control plane (runs + WS)** -> `feature/control-plane-ws`
2. **F-Stack (hash + verify)** -> `feature/fstack-verify`
3. **Provider gateway (probes)** -> `feature/providers-probe`
4. **FSPU planner v0** -> `feature/fspu-planner-v0`
5. **Web dashboard (timeline + gear)** -> `feature/dashboard-timeline`

## Acceptance Tests
- [ ] Control Plane: minimal websocket loopback verify.
- [ ] F-Stack: Hash calculation corresponds to spec.
- [ ] Gateway: Probe returns dummy latency.
- [ ] FSPU: Planner accepts manifest, returns null plan.
- [ ] Dashboard: Renders timeline skeleton.

## How to run locally
1. Ensure all zones exist: `ls -d backend fstack fspu gateway dashboard tools runs`
2. Run specs check: `ls spec/*.schema.json`
3. (Future) `npm install` in dashboard, `python` in backend.
