# The agents catalogue at specVersion 31

This directory is the agents catalogue the engine reads at specVersion 31
(preview). It holds the formats the catalogue owns (`formats/index.json`,
`classification.json`, `concept_list.json`: pure shape, each with `$schema` and
a `$id`), `bindings.json` (which attested agent serves which format for the
`generated` producer, and the custom-format agent, with no instructions) and
`agents.json` (per attested agent version, the `strictRejects` list that
step 5 of `package-format-v31.md` chapter 2 § 2.3.5, in
`consultologist-package-format`, takes from the attested definition; it sits here because an existing `agents/<name>.yaml` cannot
change without a new Foundry version). `agents/judgement.yaml` is the one new
attested agent. Run `python3 scripts/check-v31.py` to check all of it.

## Beside the catalogue at 30, not in place of it

The engine at specVersion 30 still reads `agents/formats.json`,
`agents/formats/*.json`, `agents/output-contracts.json`, `agents/schemas/*.json`
and the existing `agents/*.yaml`, so none of them changes. The
[design](https://github.com/Consultologist/Consultologist-Blazor/blob/def6f6cf/docs/customizable-workflow/package-format-v31/02-types-and-inputs.md)
has these formats "replacing `agents/formats.json`"; that happens when 30
retires, and until then both
catalogues live side by side and `scripts/check-v31.py` checks that the 30 files
are byte-identical to `origin/main`.

## What has no 31 file

30's `prose`, `rendered` and `terms_subset` formats have no file here. `prose`
is the registry's `plaintext`, `rendered` is `kind: rendered` on a node, and
`terms_subset` is an operation returning `check_result`. The registry's
built-in formats (`string`, `number`, `boolean`, `date`, `plaintext`,
`markdown_block`, `markdown_inline`, `check_result`, `judgement`) are not
repeated here; `bindings.json` names the ones a model writes.

## The version

`v2026.12.2`, in `bindings.json`, `agents.json` and every `$id`, is the
example version `package-format-v31.md` uses. The release sets the real one.

## Readings taken while writing

The judgement agent's rule for a question the text does not settle (answer
false, say so in the reason) is this catalogue's wording; the format
specification gives no such rule. `strictRejects` holds `["format"]` for every
bound agent version, from the example of what strict mode rejects in
`package-format-v31.md` chapter 2 § 2.3.5 (`format: "date"`), to be confirmed
against the provider at release.
