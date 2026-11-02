# Public technical references

Inspected 2 November 2026. Canonical file URLs and immutable commits are recorded in palantir-sources.json. All four repositories are references only; no third-party source or dataset was copied into NRS.

| Resource and pinned commit | Inspected material / reuse decision |
|---|---|
| [Ontology starter](https://github.com/palantir/ontology-starter-react-app/tree/7b31d4be74d4e584370afa795ae8520aaa2793db) | README and typed Country retrieval page show generated SDK object access and paginated results. Requires Foundry configuration. No explicit root license was located; no source copied. NRS uses its own typed graph fixture. |
| [AIP community registry](https://github.com/palantir/aip-community-registry/tree/290499c785b3738130a988e34159cb340253cb84) | Apache-2.0. Feedback Loop with AIP Evals describes flagged insurance-claim outputs and expected/actual evaluations; DevOps for AI Products describes managed development/production workflows. Marketplace enrollment is required; no standalone dataset suitable for this release was found in those examples. Original correction controls were constructed instead. |
| [Plottable](https://github.com/palantir/plottable/tree/fb876e955b0122619b9efc2028a9c4c0f1c514db) | MIT. README, dataset, bar-plot and linear-scale tests informed the separation of data, scales and numerical rendering checks. NRS uses independently written formulas and fixtures rather than copied test code. |
| [Blueprint](https://github.com/palantir/blueprint/tree/1a8977df0420a54c7dcb0ea05fc51d7bba5ce268) | Apache-2.0. README documents a React toolkit for dense application interfaces. Used as a design reference for tables, controls and navigation, not as an installed dependency or a tested comparison system. |

The comparison is architectural and qualitative. NRS execution results do not measure Palantir products, reproduce enterprise experiments or establish superiority. Public repository availability is not permission to redistribute unlicensed material. Locked npm/Python dependencies retain their package licenses; see the generated dependency inventory.
