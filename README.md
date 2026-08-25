# consultologist-agents

Agent manifests for [Consultologist](https://app.consultologist.ai) — the
canonical, git-controlled definition of every Foundry agent and the
output-contract catalog. Seeded from the app repo (Consultologist-Blazor)
on 2026-07-23; design in its `docs/customizable-workflow/content-repos.md`.

## Full GitOps

Merging to `main` IS the publish event:

- A changed `agents/{name}.yaml` → CI creates the new **Foundry agent
  version** (`POST …/agents/{name}/versions`) and asserts the returned
  version number equals the yaml's `version:`, then mirrors the
  **redacted** manifest to the registry
  (`agent-definitions/{name}/{version}/definition.yaml`).
- A changed `agents/output-contracts.json` → CI publishes the catalog
  version (schemas first, catalog last, immutable versions).

  Gated by the **stranding check** (#374): a published package version is
  immutable, but whether it still *loads* is not — the package carries a
  copy of each schema and the engine re-matches it against the live catalog
  on every load. So altering or retiring a contract can stop an
  already-published package loading, reported as "registry unavailable",
  with a new package version the only remedy. CI runs the engine's own
  `TryResolveContract` over every published public package version that
  declares a schema, on the pull request and again before the upload, and
  refuses a catalog that would strand one. Run it yourself with:

  ```
  dotnet run -v q --file <app-repo>/scripts/check-catalog-strands-packages.cs -- agents
  ```

  It does **not** cover `acct-*` forks, which live in the private account a
  public CI job cannot read.

Publishing ≠ activating: the app's `AzureAI__*Version` pins gate which
version runs. The app's startup attestation compares the deployed Foundry
agent against the registry mirror — since only this repo's CI can write
either, git is the single channel and drift is detectable by construction.

CI authenticates via GitHub→Azure OIDC (no stored secrets); human registry
writes are retired.

## Licence

The content in this repository — the agent definitions and the output-contract
catalog with its schemas — is licensed **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**
— © 2026 Tauheed Elahee: read, cite, modify for research and trial, share
alike, with attribution; not for commercial use *under this licence*. A
workflow package copies a catalog schema into its own files; the copy carries
the same permission. The licence file travels with every published version
from the first publish after 2026-08-25.

**Consultologist clients hold a licence that goes beyond this one.** Every
client may use these definitions and schemas, and the packages that copy them, commercially — inside the app, and in their own
environment outside it — and holds the copyright in what they author. That
permission is part of the client agreement, not this file; this licence is
the public default for everyone else. Anyone who needs more than it grants
can ask.

Not reached: the engine (PolyForm Strict), the Foundry deployment behind a
definition, any patent, any trademark. GitHub shows "Other": it classifies no
NonCommercial licence.
