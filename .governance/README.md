# .governance

This directory holds repository governance artifacts that are not part of the project deliverables themselves.

Current files:

- `policy-overrides.yaml`: case log for material, temporary policy overrides.
- `policy-overrides-spec.yaml`: field definitions and operating conventions for the override log.

Usage guidance:

- Keep structured fields concise and specific.
- Use `notes` only for deviations, restoration complications, or context that does not fit the standard fields.
- Prefer amending an existing override record for the same case over creating stacked or nested overrides.
- If unusual cases become common, update `policy-overrides-spec.yaml` and the relevant policy text instead of stretching ad hoc notes indefinitely.
