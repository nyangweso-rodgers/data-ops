# Architecture - PowerBI

## Table of Contents

# PowerBI Files

## .pbix — the standard Power BI file

- **Description**: The default when you hit Save in Power BI Desktop. It bundles everything into a single binary file (a zip under the hood):
  - the report (pages, visuals, formatting)
  - the semantic model (tables, relationships, DAX measures, Power Query/M code)
  - a cached copy of any imported data

- **Use it for**:
  - everyday authoring and publishing to the Power BI Service.

- **Downsides**: it can get large because the data is inside, and because it’s binary, Git can’t diff or merge it. Two people editing the same `.pbix `means one overwrites the other.

## .pbit — Power BI Template

- **Description**: This is a `.pbix` with the data removed. It keeps the report layout, the model, the queries, and the measures, but no rows. When someone opens it, Power BI refreshes the data from the sources, optionally after asking them to fill in parameters you defined (e.g., server name, region, date range).

- **Use it for**:
  - reusable report starters, like a standard KPI layout every country team fills with its own data
  - sharing a report’s design without sharing the data, which matters for sensitive or large datasets
  - tiny file sizes for emailing or storing

## .pbip — Power BI Project

- **Description**: This is the developer-friendly format. Instead of one binary file, it saves a folder of plain-text files:

  ```text
  Sales.pbip
  Sales.Report/
      definition.pbir        ← points to the model
      definition/ ...        ← pages/visuals as JSON (PBIR format)
  Sales.SemanticModel/
      definition.pbism
      definition/ ...        ← tables, measures, relationships as TMDL files
      .pbi/cache.abf         ← cached data (gitignored by default)
  ```

- **Use it for**:
  - Git version control. You can see exactly which measure or visual changed in a diff.
  - Code review and PRs on DAX and model changes
  - Multiple developers working on the same report
  - CI/CD pipelines and Fabric’s Git integration (syncing workspaces to Azure DevOps or GitHub)
  - Bulk edits by script, like renaming a column across 40 measures with find-and-replace in TMDL

- **Gotchas**:
  - The `.pbip` file is only a pointer. The real content is in the two folders, so always commit the folders.
  - Desktop creates a `.gitignore` that excludes `.pbi/cache.abf` and `.pbi/localSettings.json`. After a fresh clone there's no data until you hit Refresh.
  - `definition.pbir` can point to the model **by path** (the local `.SemanticModel` folder) or **by connection** (a semantic model already published to the Service). The second one is a "thin report": one shared model feeding many reports.
  - Desktop doesn't notice changes made outside it. Close Desktop before editing TMDL/JSON by hand (or pulling from Git), then reopen.
  - Windows has a 260-character path limit, and nested PBIR folders can hit it. Keep the repo path short.

## Converting between the three

| From → To         | How                                                                 |
| ----------------- | ------------------------------------------------------------------- |
| `.pbix` → `.pbit` | File → Export → Power BI template                                   |
| `.pbix` → `.pbip` | File → Save As → Power BI project files (`*.pbip`)                  |
| `.pbip` → `.pbix` | Open the `.pbip`, then File → Save As → `.pbix`                     |
| `.pbit` → `.pbix` | Open the `.pbit`, fill in the parameters, let it refresh, then save |

## Quick comparison

|               | `.pbix`                  | `.pbit`                             | `.pbip`                             |
| ------------- | ------------------------ | ----------------------------------- | ----------------------------------- |
| Format        | single binary (zip)      | single binary (zip)                 | folder of text files (JSON + TMDL)  |
| Contains data | yes (import mode)        | no                                  | only in the local, gitignored cache |
| Git-diffable  | no                       | no                                  | yes                                 |
| Typical use   | authoring and publishing | reusable starters, sharing a design | team development, CI/CD             |

## Things true for all three

- **Credentials are never saved in the file.** Whoever opens it signs in to the sources themselves, and the Service keeps credentials separately on the semantic model / gateway.
- **RLS roles travel with the model, but role membership doesn't.** You assign users to roles in the Service after publishing.
- **Storage mode decides the size.** Import mode stores data in the model. DirectQuery or Live Connection models hold no rows, so even a `.pbix` stays small.
- **Publish size limit:** 1 GB per `.pbix` on Pro. Premium/Fabric capacities allow more, and large models should use incremental refresh rather than shipping data in the file.
- **Tools that work on the model outside Desktop:** Tabular Editor (2 free / 3 paid), DAX Studio, and the VS Code TMDL extension for `.pbip` projects.

# Resources and Further Reading
