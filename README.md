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
