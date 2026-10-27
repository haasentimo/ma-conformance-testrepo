# depot — synthetic test repository for architecture conformance checking

`depot` is a small, synthetic Python code base built for the Z3 study of the master thesis of
Timo Haas (HTWG Konstanz). The study asks whether a checker detects architecture violations that
were injected on purpose. The repository contains one clean **baseline** and **32 injection
states**. Each injection state introduces one targeted architecture violation on top of the
baseline. The repository is a measurement subject, not an application.

> [!IMPORTANT]
> **The measured states are the tags, not `main`.** `baseline` and `inj/01` … `inj/32` point to
> exactly the commits that were measured, and they are never moved or rewritten. Up to and
> including the measurement, `main` pointed to the baseline. Since the documentation update that
> added this README and the license, `main` is one commit ahead and **no longer** points to the
> measured baseline.

> [!NOTE]
> **Published after the measurement.** The repository was private from its creation (14.08.2026)
> through the Z3 evaluation (27.–28.08.2026). Models trained after the publication date may have
> seen this code.

## Baseline (`baseline` = `0d65104`)

- `src/depot/` contains 73 Python files. There is a shared `core/` (ports, errors, config, an
  adapter facade with protected `internal/` modules) and three contexts: `identity/`, `orders/`
  and `billing/`. Each context has the layers `api/` → `services/` → `repository/`, plus
  `models/` and `mappers/`.
- The permitted dependencies between these components form the target architecture (the target
  model). Its machine-readable form is in `master-thesis-artifacts` (see below).
- During Z3 the code was analysed, never run as an application. It has no entry point, no
  composition root, no database and no tests. The `models` modules are annotation-shaped
  SQLAlchemy classes without a declarative base.
- The individual modules can be imported. With Python 3.12 and `SQLAlchemy==2.0.52`, every
  module of the baseline and of all 32 injection states imports without error.
- The `README.md` in the baseline commit is the historical one from the time of measurement. It
  refers to planning documents of the thesis repository, which is not public.

## Injection states (`inj/01` … `inj/32`)

Every injection is one commit whose parent is the baseline (a star, not a chain). It changes
exactly one file, the carrier module, and introduces one targeted architecture violation. No
injection builds on another.

A single injection is not limited to a single finding. Depending on the checker, the same change
can also be reported by further rules or as several findings. One example is a cycle that is
reported for both components. The expected findings per injection, including registered
co-findings, are listed in the injection manifest.

| Scenario | Count | Targeted violation |
|---|---|---|
| `LAYER_BACK_CALL` | 3 | a lower layer imports a higher one |
| `LAYER_SKIP_CALL` | 3 | `api` bypasses `services` and reaches a repository |
| `PROTECTED_MODULE` | 3 | a service uses an internal adapter module directly |
| `INDEPENDENCE` | 3 | one context reaches into another |
| `CYCLE_SIBLING` | 3 | an import cycle between sibling components |
| `CYCLE_PARENT_CHILD` | 1 | an import cycle between a package and its child |
| `MISSING_PORT_REFERENCE` | 4 | a service signature loses its port parameter |
| `FRAMEWORK_TYPE_IN_SIGNATURE` | 4 | a persistence type appears in a model signature |
| `INCORRECT_LOCATION` | 4 | a module is moved out of its package (pure rename) |
| `SIGNATURE_DEVIATION` | 4 | a method signature deviates from the target model |

The violations are deliberate. Because nothing is wired together, all states remain importable.
Some injections would break their call sites if the code were ever assembled and run: removed
port parameters, changed signatures and moved modules.

<details>
<summary>All 32 injection tags with commit and changed file</summary>

| Tag | Commit | Scenario | Changed file (under `src/depot/`) |
|---|---|---|---|
| `inj/01` | `439125e` | LAYER_BACK_CALL | `identity/repository/customer_repo.py` |
| `inj/02` | `4165fab` | LAYER_BACK_CALL | `orders/repository/order_repo.py` |
| `inj/03` | `b3fb129` | LAYER_BACK_CALL | `billing/repository/invoice_repo.py` |
| `inj/04` | `3de8357` | LAYER_SKIP_CALL | `identity/api/routes.py` |
| `inj/05` | `dbcd05b` | LAYER_SKIP_CALL | `orders/api/routes.py` |
| `inj/06` | `531a1ff` | LAYER_SKIP_CALL | `billing/api/routes.py` |
| `inj/07` | `0993e01` | PROTECTED_MODULE | `identity/services/customer_service.py` |
| `inj/08` | `792cb68` | PROTECTED_MODULE | `orders/services/order_service.py` |
| `inj/09` | `06e052e` | PROTECTED_MODULE | `billing/services/invoice_service.py` |
| `inj/10` | `e182964` | INDEPENDENCE | `orders/services/checkout_service.py` |
| `inj/11` | `5601a94` | INDEPENDENCE | `billing/services/dunning_service.py` |
| `inj/12` | `cb1fb22` | INDEPENDENCE | `orders/repository/order_line_repo.py` |
| `inj/13` | `3be646f` | CYCLE_SIBLING | `identity/mappers/customer_mapper.py` |
| `inj/14` | `a9d6445` | CYCLE_SIBLING | `orders/mappers/order_mapper.py` |
| `inj/15` | `616cb02` | CYCLE_SIBLING | `billing/mappers/invoice_mapper.py` |
| `inj/16` | `43f9fa5` | CYCLE_PARENT_CHILD | `orders/services/pricing/engine.py` |
| `inj/17` | `c5faa0a` | MISSING_PORT_REFERENCE | `identity/services/token_service.py` |
| `inj/18` | `ad21063` | MISSING_PORT_REFERENCE | `orders/services/catalog_service.py` |
| `inj/19` | `864da96` | MISSING_PORT_REFERENCE | `orders/services/refund_service.py` |
| `inj/20` | `35061d8` | MISSING_PORT_REFERENCE | `billing/services/ledger_service.py` |
| `inj/21` | `dd41465` | FRAMEWORK_TYPE_IN_SIGNATURE | `identity/models/customer_models.py` |
| `inj/22` | `08a622b` | FRAMEWORK_TYPE_IN_SIGNATURE | `orders/models/order_models.py` |
| `inj/23` | `28a7574` | FRAMEWORK_TYPE_IN_SIGNATURE | `orders/models/order_line_models.py` |
| `inj/24` | `91ed6a8` | FRAMEWORK_TYPE_IN_SIGNATURE | `billing/models/invoice_models.py` |
| `inj/25` | `ef11480` | INCORRECT_LOCATION | `orders/repository/legacy_order_index.py` → `orders/legacy_order_index.py` |
| `inj/26` | `efe5c81` | INCORRECT_LOCATION | `billing/repository/legacy_invoice_index.py` → `billing/legacy_invoice_index.py` |
| `inj/27` | `33ad86a` | INCORRECT_LOCATION | `identity/repository/legacy_token_index.py` → `identity/legacy_token_index.py` |
| `inj/28` | `72dc746` | INCORRECT_LOCATION | `billing/models/legacy_tax_models.py` → `billing/legacy_tax_models.py` |
| `inj/29` | `5e685cf` | SIGNATURE_DEVIATION | `identity/repository/session_repo.py` |
| `inj/30` | `604d304` | SIGNATURE_DEVIATION | `orders/repository/order_query.py` |
| `inj/31` | `3d33745` | SIGNATURE_DEVIATION | `billing/repository/invoice_query.py` |
| `inj/32` | `307e573` | SIGNATURE_DEVIATION | `orders/mappers/order_line_mapper.py` |

</details>

## Using it

```bash
git clone https://github.com/haasentimo/ma-conformance-testrepo.git
cd ma-conformance-testrepo
git checkout baseline          # the measured clean state (detached HEAD)
git checkout inj/07            # one injection state (detached HEAD)
git diff baseline inj/07       # exactly the injected change
git checkout main              # back to the documentation state
```

`git clone` fetches the tags. In an existing clone, use `git fetch --tags`.

## Relation to the thesis and `master-thesis-artifacts`

[`master-thesis-artifacts`](https://github.com/haasentimo/master-thesis-artifacts) is the
evidence package of the thesis. For this repository it holds:

- [`data/soll/`](https://github.com/haasentimo/master-thesis-artifacts/tree/main/data/soll) — the
  target model: [architecture rules](https://github.com/haasentimo/master-thesis-artifacts/blob/main/data/soll/architecture-rules.yaml),
  [Ilograph model](https://github.com/haasentimo/master-thesis-artifacts/blob/main/data/soll/depot_soll.ilograph.yaml),
  import-linter contract, architecture test and control file list
  ([index](https://github.com/haasentimo/master-thesis-artifacts/blob/main/data/soll/MANIFEST.md));
- the injection manifest ([`injection_manifest.md`](https://github.com/haasentimo/master-thesis-artifacts/blob/main/data/soll/injection_manifest.md),
  machine-readable [`injection_manifest.json`](https://github.com/haasentimo/master-thesis-artifacts/blob/main/data/soll/injection_manifest.json)):
  scenario, carrier module, rule and expected findings for every injection, keyed by tag and
  commit;
- [`data/testrepo/`](https://github.com/haasentimo/master-thesis-artifacts/tree/main/data/testrepo)
  — git bundles of exactly these refs (baseline and the 32 injection tags) with SHA256, so the
  measured states remain verifiable independently of this repository;
- [`data/campaign/`](https://github.com/haasentimo/master-thesis-artifacts/tree/main/data/campaign)
  — the raw results of the five checker configurations per injection, and the canonical
  evaluation [C14](https://github.com/haasentimo/master-thesis-artifacts/blob/main/data/campaign/eval/c14_eval_full.md).

## License

Released under the MIT License, see [`LICENSE`](LICENSE). The license file was added with the
documentation update; it covers the code of all states, including the tagged measured commits.
