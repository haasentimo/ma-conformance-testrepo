# depot — synthetic evaluation dataset

**Purpose.** This repository is the evaluation dataset of phase 04 of a master's thesis at
HTWG Konstanz. It is a synthetic, contamination-free test repository built solely to be measured
against a target architecture model. It is not a product, not a library, and it is not intended
to be used by anyone for anything else.

**Author.** Timo Haas. **Created.** 14 August 2026.

## Provenance

No code in this repository was taken from a public source, from a code-hosting platform, from a
model's output pasted verbatim, or from any existing production or private system. Every module,
class, function name, docstring and comment was written for this dataset. The domain — a parcel
depot with acceptance, storage, shipping orders and invoicing — was chosen deliberately so that
it does not resemble the system whose measured structure informed the target model.

This repository is held in a **private** repository and has never been publicly accessible. It
was created private and has stayed private since the first commit.

## What this code is

The code is a **measurement subject**, not a runnable application. It has no entry point, no
composition root, no configuration loading, no database and no tests, and none of these are
missing by oversight — each is an explicit design decision recorded in the specification.

In particular, the `models` modules are **annotation-shaped**: they declare persistence-typed
class attributes and call the corresponding column constructors, but they deliberately carry
**no declarative base class**. A shared base would have to live in a module every context can
import, which would put a persistence framework import into the core — and the core is required
to stay framework-free. The classes therefore describe a mapping without being attached to a
registry. All modules import cleanly under the framework version the specification pins; none of
them is executed.

## Specification

The structure of this repository is not free. Every file, its component, its outgoing imports and
the permitted relations between components are laid down in the thesis repository:

- `docs/planung/c1_modulliste.md` — the package and module list, including the exact set of
  outgoing imports per module
- `docs/planung/c1_komponentenschnitt.md` — the component cut and the whitelist of permitted
  relations

Anything in this repository that deviates from those two documents is a defect in this
repository, not a variant.

Files that are not `.py` — this README and `.gitignore` — are outside the target model and are
not part of the comparison.

## This commit

This commit is the clean baseline **`B`**, tagged `baseline`. It is the state the whole
evaluation is measured against, and the state every later commit of the campaign is compared to:
those commits hang off this one in a star, each a single self-contained change on top of `B`,
none of them building on each other.
