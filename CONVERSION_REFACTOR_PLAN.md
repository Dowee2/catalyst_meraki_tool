# Conversion Refactor Plan: Device-Type-Based → Interface-Pattern-Based

## Problem

The conversion script currently requires the user to manually select a device type (2960 or 3850) in the wizard UI. This selection only controls how interface names are parsed. The device type is really just a proxy for the interface naming format:

- **3-part**: `GigabitEthernet1/0/1` (switch/group/port) — 1-based switch indexing
- **2-part**: `GigabitEthernet1/1` (switch/port) — 0-based switch indexing

## Goal

Remove the device type selection entirely. Auto-detect the interface format by examining the interface names in the config. Also expand support beyond just `GigabitEthernet` to all known Ethernet prefixes.

## Current Architecture (How device_type flows)

```
ConversionWizard (UI radio: '2960'/'3850')
  → wizard_data['switch_type']
    → ConversionController.run_conversion()
      → device_type = 'catalyst_3850' if switch_type == '3850' else 'catalyst_2960'
        → convert_module.run(device_type=...)
          → map_interface_configs(device_type=...)
            → InterfaceParser.parse_interface(intf_name, device_type)
            → valid_interface(device_type=...)
            → serial indexing: [switch_number - 1] vs [switch_number]
```

The `device_type` controls exactly 3 behaviors:
1. **Regex pattern**: 3-part `(\d+)/(\d+)/(\d+)` vs 2-part `(\d+)/(\d+)`
2. **Switch index base**: 1-based (subtract 1 for serial lookup) vs 0-based (direct)
3. **Access group filtering**: 3-part has a middle "group" number that must match; 2-part has none

## Key Design Decisions

- **Auto-detection**: Scan ALL interface names. Try 3-part regex first, then 2-part. Each interface is processed according to its own detected format.
- **Indexing**: 3-part → 1-based, 2-part → 0-based (inherent to the Cisco naming convention)
- **Mixed formats**: Process each interface individually (try 3-part first, fall back to 2-part)
- **Access group**: Keep filtering for 3-part interfaces (default group=0)
- **Ethernet prefixes to support**: GigabitEthernet, FastEthernet, TenGigabitEthernet, TwentyFiveGigE, FortyGigabitEthernet, HundredGigE (and abbreviations: Gi, Fa, Te, Twe, Fo, Hu)

---

## Implementation Steps (in order)

### Step 1: `utils/interface_parser.py` — Add auto-detection

Current patterns (lines 22-39) are keyed by device type. Add new pattern-based approach.

**Add at module level:**
- `ETHERNET_PREFIXES` tuple — all known prefixes sorted longest-first to avoid partial regex matches
- `PATTERN_THREE_PART` — compiled regex: `(?:HundredGigE|TwentyFiveGigE|FortyGigabitEthernet|TenGigabitEthernet|GigabitEthernet|FastEthernet|Hu|Twe|Fo|Te|Gi|Fa)(\d+)/(\d+)/(\d+)`
- `PATTERN_TWO_PART` — same prefix group but `(\d+)/(\d+)$` (note `$` anchor to prevent partial match on 3-part names)

**Add `FormatType` enum:**
- `THREE_PART` and `TWO_PART` values

**Add `InterfaceFormat` dataclass:**
- `format_type`: FormatType
- `switch_index_base`: int (1 for three-part, 0 for two-part)
- `has_access_group`: bool
- `three_part_count`: int
- `two_part_count`: int

**Add new classmethods to `InterfaceParser`:**

```python
@classmethod
def detect_format(cls, interface_names: list) -> Optional[InterfaceFormat]:
    """Scan all interface names, return detected format info or None."""
    # Count 3-part vs 2-part matches. Return format with majority.

@classmethod
def parse_interface_auto(cls, interface_name: str) -> Optional[Tuple]:
    """Parse without device_type. Try 3-part first, then 2-part.
    Returns: ('three_part', switch, group, port) or ('two_part', switch, port) or None"""
```

**Also expand** `get_interface_prefix()` (line 154) to include all new prefixes.

**Keep all existing methods intact** — the comparison scripts still use them.

### Step 2: `config/constants.py` — Remove device type mapping

- **Remove** `DEVICE_INTERFACE_PATTERNS` dict (lines 54-57) — no longer needed

### Step 3: `scripts/convert_catalyst_to_meraki.py` — Core refactor

**`valid_interface()` (line 81):**
- Replace `device_type` param with `is_one_based: bool`
- Same logic but driven by bool instead of string comparison

**`map_interface_configs()` (line 113):**
- Remove `device_type` param
- Call `InterfaceParser.detect_format()` at the start for logging
- Loop: for each interface, call `InterfaceParser.parse_interface_auto()`
  - If result is `None` → skip (non-Ethernet interface like Vlan, Loopback)
  - If `'three_part'` → extract switch/group/port, filter by access_group, 1-based serial lookup
  - If `'two_part'` → extract switch/port, 0-based serial lookup
- Remove the `if not intf_name.startswith('GigabitEthernet')` filter (line 132) — the regex handles this now

**`run()` (line 188):**
- Remove `device_type` param from signature
- Add `**kwargs` to accept deprecated `device_type` calls without crashing
- Remove `device_type` from `map_interface_configs()` call

### Step 4: `controllers/conversion_controller.py` — Remove device_type plumbing

**`run_conversion()` (line 34):**
- Remove: `switch_type = wizard_data.get('switch_type', '2960')` (line 57)
- Remove: `device_type = 'catalyst_3850' if switch_type == '3850' else 'catalyst_2960'` (line 64)
- Remove `device_type` from `_run_ip_conversion()` and `_run_file_conversion()` calls

**`_run_ip_conversion()` (line 88):**
- Remove `device_type` from signature
- Remove `f"Device type: {device_type}\n"` console line
- Remove `device_type=device_type` from `convert_module.run()` call

**`_run_file_conversion()` (line 141):**
- Same changes as above

### Step 5: `views/wizards/conversion_wizard.py` — Remove switch type UI

- Remove `'switch_type': '2960'` from `wizard_data` dict (line 63)
- Remove `self.switch_type_var = None` from UI references (line 73)
- In `_create_destination_step()`: remove `self._create_switch_type_section(content_frame)` call
- **Delete entire** `_create_switch_type_section()` method
- In `_save_destination_data()`: remove `self.wizard_data['switch_type'] = self.switch_type_var.get()`
- In `_update_review_summary()`: replace `f"Switch type: Catalyst {data['switch_type']} Series"` with `"Interface format: Auto-detected from configuration"`

### Step 6: `config/script_types.py` — Minor cleanup

- Remove `from_device_type()` classmethod (lines 29-42) — dead code

---

## Reference: Current Interface Patterns

| Pattern | Example | Components | Switch Index | Serial Lookup |
|---------|---------|-----------|--------------|---------------|
| 3-part | `GigabitEthernet1/0/1` | switch=1, group=0, port=1 | 1-based | `serials[switch - 1]` |
| 2-part | `GigabitEthernet0/1` | switch=0, port=1 | 0-based | `serials[switch]` |

## Reference: Ethernet Prefixes

Full names: `GigabitEthernet`, `FastEthernet`, `TenGigabitEthernet`, `TwentyFiveGigE`, `FortyGigabitEthernet`, `HundredGigE`

Abbreviations: `Gi`, `Fa`, `Te`, `Twe`, `Fo`, `Hu`

## Verification

1. Test with a 2960-style config (GigabitEthernet1/0/X) — should auto-detect 3-part
2. Test with a 3850-style config (GigabitEthernet0/X) — should auto-detect 2-part
3. Wizard Step 3 no longer shows switch type radio buttons
4. Review summary says "Auto-detected" instead of switch type
5. Run app end-to-end through wizard — no crashes
