# Website consumer behavior

| Attribute | Value |
|-----------|--------|
| Status | **SPECIFIED / NOT IMPLEMENTED** |
| Date | 2026-09-26 |
| Engine | `concrete_slab` `1.0.0` |
| Live site | Not changed by this specification |

The consumer presents a result. It does not change inputs, assumptions, components, or quantities. Consumer metadata sits outside the Contract V1 object and outside the calculation fingerprint.

## Optional project or reference name

The person may type a project or reference name. It may be left blank.

The name is consumer metadata. It is not an input. It does not change the fingerprint. It is shown on the summary, included in a save, and included in a download.

The field does not ask for an account, an email address, a phone number, or a company.

## Calculation Summary

The summary is the professional on-page presentation of one run. It shows:

- CalibraytAI
- the title Calculation Summary
- the project or reference name when one was entered
- engine `concrete_slab`, version `1.0.0`, and the variant in plain language (`standard` or thickened edge)
- the measurement system
- each input with its unit
- the waste assumption
- each component with its quantity and unit
- the total concrete quantity and unit
- a statement that the page is a quantity calculation, not a price, not an engineering design, and not a proposal

The summary does not show a unit cost, a sell price, a margin, or a company name as the author of the quantities.

## Save on This Device

Save writes the Contract V1 result and the consumer metadata onto that browser on that device.

- No account.
- No server copy in this programme.
- Clearing the site data on that browser clears the save.
- A later run is a new result with a new `result_id`. Save does not overwrite the calculation identity of an older run. The device may keep more than one saved result.

## Download Calculation

Download delivers a file the person keeps. The file contains two objects and does not merge them:

- `calculation_result`: the Contract V1 payload
- `consumer_metadata`: the optional project or reference name, and local presentation fields defined in the [platform handoff](platform-handoff.md)

The professional summary is the human reading of that same run. Download does not require an account and does not add a price.

## What the consumer does not do

- It does not publish this specification to the live site.
- It does not call the Platform.
- It does not create an estimate, a project record, or a user account.
