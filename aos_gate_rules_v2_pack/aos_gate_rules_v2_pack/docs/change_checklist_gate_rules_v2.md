# Change Checklist — Kernel Gate Rules v2 (Production)

## Contract
- [ ] `policy_mode` present (`enforce` vs `audit_only`)
- [ ] `defaults.on_missing_gate` set (`deny|halt|revise`)
- [ ] Each rule includes `applies_to.phases` (>=1)
- [ ] Each rule includes `authority` and `decision_requirements`
- [ ] `decision_requirements.requires_ledger_event == true`
- [ ] Evidence requirements are explicit (`min_evidence`, `required_evidence_types`)

## Runtime enforcement expectations
- [ ] Runtime must block phase transitions when a required gate is unmet
- [ ] Gate decision must emit a ledger event (`decision_event_type`)
- [ ] Missing-gate behavior follows `defaults.on_missing_gate`
- [ ] Deny/halt behavior follows `runtime_effect` (or safe default)

## Testing
- [ ] Unit test: required gate missing -> expected default outcome
- [ ] Unit test: deny_is_terminal -> scene halted
- [ ] Replay test: same ledger -> same gate outcomes (no hidden state)
