# Repository Review — Group 7

**Course:** Applied Datateknik, Mid Sweden University  
**Group:** 7  
**Project name:** Dynamic Persona Mapping for Social Media Insights  
**Repository:** https://github.com/KimEnflo/DT002G-Project  
**Review date:** 2026-03-04  
**Reviewer:** GitHub Copilot (automated evidence-based review) Claude Sonnet 4.6 

---

## 1. Repository Summary

### Project purpose
A command-line tool that scrapes Reddit threads, cleans and tokenizes the collected comments, and is intended to classify users into predefined personas based on keyword rules. The final output is a JSON file.

### Technology stack
Python 3.12, httpx (HTTP client for Reddit JSON API), BeautifulSoup4 + markdown2 (HTML/Markdown cleaning), spaCy `en_core_web_lg` (NLP), Playwright (listed in requirements but not used in code).

### Current development state
The scraping, cleaning, and output-saving pipeline is functional. The persona classification step — the core purpose of the project — is not implemented: `persona_rules` is loaded in `parse()` but never passed to or used by the tokenizer or any classifier. The tokenizer module calls `nlp()` but discards the result, so spaCy processing has no effect on output. The project is therefore partially complete.

---

## 2. Evidence-Based Checklist of Good Practices

Scale: **Yes / Partly / No / Unclear**

### 2.1 Structure and organization

**The repository has a clear and logical folder structure.**  
Assessment: Yes  
Evidence: Root contains `persona_parser.py` (entry point), `tokenizer.py`, and subdirectories `scrapers/`, `text_cleaners/`, `resources/`.  
Comment: The separation of concerns across folders is sensible and easy to navigate.  

**Source code, tests, configuration, and documentation are separated appropriately.**  
Assessment: Partly  
Evidence: Source is modularised; `resources/persona_specifications.json` acts as configuration. There is no `tests/` folder anywhere in the repository.  
Comment: Configuration and source are reasonably separated, but the complete absence of any test directory is a significant gap.  

**File and folder names are meaningful and consistent.**  
Assessment: Yes  
Evidence: `scrapers/reddit_scraper.py`, `text_cleaners/reddit_text_cleaner.py`, `resources/persona_specifications.json` — all names reflect their content.  
Comment: Naming is clear and follows a consistent `<platform>_<role>.py` pattern.  

**The repository avoids unnecessary generated files or clutter.**  
Assessment: Yes  
Evidence: A comprehensive `.gitignore` (208 lines, standard Python template) is present. No `__pycache__`, `.egg-info`, or `venv` directories are committed.  
Comment: The repository is clean.

### 2.2 Code quality

**The code appears correct and runnable.**  
Assessment: Partly  
Evidence: The scraping and cleaning pipeline (`reddit_scraper.py`, `reddit_text_cleaner.py`) is self-contained and appears runnable. However, `tokenizer.py` calls `nlp(comments[comment]["text"])` but never assigns or returns the result — the spaCy processing is silently discarded. Additionally, `load_persona_specifications()` return value is assigned to `persona_rules` in `parse()` but never used.  
Comment: The scraping and cleaning steps appear functional, but the NLP tokenisation and persona classification are not wired up. These are not minor gaps — they represent the core data processing and classification requirements.  

**The code follows consistent style and coding conventions.**  
Assessment: Yes  
Evidence: Docstrings are present on every function, type hints are used throughout (`list`, `dict`, `str`, `Generator`), and imports are ordered consistently.  
Comment: The code reads consistently across all modules.  

**The code is readable and reasonably modular.**  
Assessment: Yes  
Evidence: Each module has a single responsibility. `reddit_scraper.py` handles fetching; `reddit_text_cleaner.py` handles sanitising; `tokenizer.py` is intended for NLP; `persona_parser.py` is the orchestrator. Functions are short and well-named.  
Comment: Good modular design. The separation makes it easy to extend or replace individual steps.  

**There are no major obvious code smells (duplication, overly large files, unclear naming).**  
Assessment: Partly  
Evidence: No duplication or overly large files. However, the `tokenizer.py` dead-code bug (result of `nlp()` discarded, loop iterates but does nothing useful) and the unused `persona_rules` variable in `persona_parser.py` are functional code smells.  
Comment: The structural code quality is good, but the silent no-ops in the processing pipeline are a notable issue that would be easy to miss without running the code.

### 2.3 Documentation

**The repository contains a clear README.**  
Assessment: Yes  
Evidence: `README.md` exists at the repository root with sections for limitations, installation, and usage.  
Comment: Concise and well-structured for a project of this scope.  

**The README explains how to install, run, and use the system.**  
Assessment: Yes  
Evidence: README covers Python 3.12 installation, venv creation (Windows and macOS/Linux), `pip install -r requirements.txt`, and the exact command `python persona_parser.py reddit <URL>` with an example.  
Comment: A new developer can get started from the README alone.  

**The documentation would help a new developer understand and contribute to the project.**  
Assessment: Partly  
Evidence: Installation and running are covered. Docstrings on all functions aid code-level understanding. However, there is no explanation of how to add a new platform (e.g., Twitter), how persona rules work, or what the output JSON structure looks like.  
Comment: Good starting point, but contributing documentation (architecture overview, how to extend personas) is missing.  

**Important design decisions or setup details are documented.**  
Assessment: Partly  
Evidence: The README notes the API throttling limitation (~1,500 comments) and suggests keeping threads to ≤1,000 comments. The `persona_specifications.json` file is self-explanatory but not described in the README.  
Comment: The key operational limitation is documented, which is good. The persona rule format and the intended output structure could be documented to aid future development.

### 2.4 Testing

**The repository contains tests.**  
Assessment: No  
Evidence: No `tests/` folder and no `test_*.py` files anywhere in the repository. No `pytest.ini`, `setup.cfg`, or `pyproject.toml` with test configuration.  
Comment: This is a significant gap. The project has runnable logic (scraping, cleaning, tokenising) that would be straightforward to unit-test.  

**Tests are relevant to the main functionality.**  
Assessment: No  
Evidence: No tests exist.  
Comment: N/A — see above.  

**Tests can be executed with clear instructions.**  
Assessment: No  
Evidence: No tests exist; no test runner instructions in README.  
Comment: N/A.  

**Tests appear to pass, or there is evidence that they have been run successfully.**  
Assessment: No  
Evidence: No tests exist; no CI configuration (no `.github/workflows/` directory).  
Comment: N/A.

### 2.5 Collaboration and development practices

**Commit history suggests incremental development.**  
Assessment: Yes  
Evidence: 13 commits total. Development follows a clear feature-by-feature progression: initial commit → reddit parser (PR #1) → tokenizer (PR #2) → text cleaner (PR #3) → tokenizer revamp (PR #4) → persona loader (PR #5).  
Comment: The use of feature branches, pull requests, and merge commits demonstrates a disciplined incremental workflow.  

**Commit messages are meaningful.**  
Assessment: Partly  
Evidence: Messages include "Add reddit parser", "Add reddit_tex_cleaner", "add loading person specification feature and saving output." — contextual but brief. Some are generic: "Update README.md" (×2), "Updated tokenizer.py".  
Comment: Most messages convey what changed. Typo in one message ("reddit_tex_cleaner"). Messages could be more descriptive about *why* changes were made, not just *what*.  

**There is evidence of collaboration between both students.**  
Assessment: No  
Evidence: `git shortlog -sn --all` shows two name variants — "KimEnflo" (8 commits) and "Kim" (5 commits) — both resolving to the same GitHub account (KimEnflo). No commits from a second author appear anywhere in the history.  
Comment: All visible work comes from one student. If the second student contributed, it is not reflected in the commit history under their own account. This should be clarified with the group.

---

## 3. What Is Being Done Well

1. **Good modular structure.** The codebase is split into single-responsibility modules (`scrapers/`, `text_cleaners/`, `tokenizer.py`) that are easy to navigate and extend.
2. **Consistent code style.** All functions have docstrings, type hints are used throughout, and naming is clear and consistent.
3. **Feature-branch workflow with pull requests.** Five PRs merged into `main` via feature branches show a professional Git workflow for a two-person project.
4. **Clear README with a concrete usage example.** The README documents setup, venv activation for both Windows and macOS/Linux, and the exact CLI command with a URL example.
5. **Rate-limit awareness.** `reddit_scraper.py` implements adaptive sleep timing and batch sizing based on comment count, and the README documents the ~1,500-comment practical limit.

---

## 4. What Needs Improvement

1. **Persona classification is not implemented.** `persona_rules` is loaded in `parse()` but never used. The project's core requirement (FR-3, FR-4, FR-5) — classifying users by keyword-based rules — is entirely missing from the codebase.
2. **The tokenizer is a no-op.** `tokenizer.py` calls `nlp(comment["text"])` but discards the spaCy document. The function returns the input unchanged, meaning no NLP processing actually occurs.
3. **No tests at all.** The repository has no test files, no test runner configuration, and no CI. The cleaning and scraping logic would be straightforward to unit-test with sample inputs.
4. **No evidence of contribution from the second student.** All 13 commits originate from a single GitHub account. If pair programming or offline collaboration occurred, it is invisible in the repository.
5. **Output is not persona-structured JSON.** `save_output()` writes tokenized comment data to `resources/matched_personas.json`, but since classification is not implemented, the file does not contain persona assignments (FR-6, NFR-4).

---

## 5. Evaluation Against Requirements

### 5.1 Functional Requirements

| Requirement | Description | Status | Evidence | Comment |
|---|---|---|---|---|
| FR-1 | Retrieve publicly available Reddit comments from specified threads. | Yes | `scrapers/reddit_scraper.py` fetches thread JSON via `httpx`, recursively expanding `more` nodes. | Fully implemented, including pagination and rate-limit handling. |
| FR-2 | Preprocess retrieved textual data using tokenization and text normalization with an open-source NLP library. | Partly | `reddit_text_cleaner.py` normalises HTML, strips URLs and whitespace using spaCy-adjacent tools. `tokenizer.py` imports spaCy but the `nlp()` result is discarded. | Cleaning is done; actual spaCy NLP processing (lemmatisation, etc.) has no effect on the output. |
| FR-3 | Allow definition and modification of persona classification rules. | Partly | `resources/persona_specifications.json` is a JSON config with persona descriptions and keywords. | The file can be edited manually, but there are no instructions for doing so and no validation of the format. |
| FR-4 | Classify users into predefined personas based solely on rule-based logic. | No | `persona_rules` is loaded in `parse()` but never passed to or used by any function. No classifier exists. | This is the core feature of the project and is not yet implemented. |
| FR-5 | Store persona classification results for each analyzed user. | No | `save_output()` saves tokenized data to `resources/matched_personas.json`, but there is no per-user persona assignment in it. | Depends on FR-4. |
| FR-6 | Generate a structured output summarizing persona assignments and distributions. | Partly | JSON output is produced, but it contains raw tokenized comment text, not persona summaries or distributions. | The output pipeline exists; the content needs to be driven by classification. |
| FR-7 | Allow users to specify topics or keywords used in persona rule evaluation. | Partly | Keywords live in `persona_specifications.json` and could be edited before a run. The CLI does not expose keyword overrides directly. | Keywords are externally configurable in principle but not usable since classification is not implemented. |
| FR-8 | Restrict data processing to text-based content from Reddit only. | Yes | The tool only accepts `reddit` as a platform argument; code only calls Reddit-specific scrapers. | Appropriately scoped. |
| FR-9 | Retrieve publicly available posts and comments from a specified Reddit user account. | No | Only thread URLs are supported. There is no user-account scraping endpoint or function. | Missing entirely; the scraper targets thread JSON, not user profile pages. |

### 5.2 Non-Functional Requirements

| Requirement | Description | Status | Evidence | Comment |
|---|---|---|---|---|
| NFR-1 | Process and classify at least 1,000 Reddit comments within 60 seconds on a standard machine. | Unclear | `persona_parser.py` prints elapsed time, but no performance test or benchmark result is committed. | Cannot be verified without running the tool against a 1,000-comment thread. |
| NFR-2 | Support batch processing of user data without requiring manual intervention during execution. | Partly | The pipeline runs end-to-end from a single command without user interaction. However, classification (the processing step) is not implemented. | The pipeline is automated; the meaningful processing step is missing. |
| NFR-3 | Provide clear configuration instructions for defining and modifying persona rules. | No | README does not mention `persona_specifications.json` or explain how to add/modify persona rules. | Instructions are needed: what fields are required, what keyword format is valid, where to find the file. |
| NFR-4 | Produce structured output in a human-readable JSON format. | Partly | Output is written to `resources/matched_personas.json` with `indent=4`, which is human-readable. Content is tokenized comment data rather than persona assignments. | Format is correct; content needs to reflect classification results. |
| NFR-5 | Provide meaningful error messages when invalid input parameters are supplied. | Partly | A usage message is printed when fewer than 3 CLI arguments are provided. `AssertionError` is caught and printed. No validation on URL format or platform string. | Error handling covers the minimum; invalid URLs or unsupported platforms would produce unguided Python tracebacks. |
| NFR-6 | Access only publicly available Reddit data through approved data access methods. | Yes | Uses Reddit's public `.json` endpoint (appending `.json` to thread URLs) and the `morechildren` API without OAuth. | Appropriate for public data access. |
| NFR-7 | Not store private user data within output files. | Partly | Outputs comment text and nested quotes. Usernames (`author` field) from the `comment_data` dict are not explicitly extracted into output. | Full comment data available in `comment_data`; confirm that `author` fields are not included in `save_output` content (currently only `text`/`quotes` keys are stored). |
| NFR-8 | Handle missing, deleted, or malformed Reddit content without terminating unexpectedly. | Partly | `filter_comments()` removes deleted/removed/bot comments. `fetch_more_children()` catches `httpx.RequestError` and JSON parse errors and continues. | Empty/malformed replies at the top-level parse step are not explicitly caught and could still raise exceptions. |
| NFR-9 | Log processing errors without interrupting the classification of remaining valid data. | Partly | Errors in `fetch_more_children()` are printed and the loop `continue`s. No structured logging (no log file, no logging module). | Errors are non-fatal, which is good. Adopting the `logging` module would provide timestamps and severity levels as expected by this requirement. |

---

## 6. Overall Assessment

### Summary judgment
The project has a solid foundation: the repository is well-structured, the code is readable and modular, and the Git workflow (feature branches, PRs) is commendable. The scraping and cleaning stages appear functional. However, the project's core purpose — persona classification — is entirely absent. The `persona_rules` loaded at startup are never used, and the tokenizer performs no actual NLP output. Combined with a complete lack of tests and commits from only one student, the project is currently at an early-to-mid stage and needs significant development to meet its requirements.

### Confidence in this review
High for structure, documentation, code quality, and FR coverage. Medium for runtime correctness (code was not executed). Low for performance (NFR-1) — cannot be assessed without running against a real dataset.

### Limitations of this review
The code was not executed. Runtime behaviour (actual output, error handling edge cases, performance) cannot be confirmed. It is not possible to determine whether the second student contributed through means not visible in Git (e.g., pair programming in-person, code review comments, or commits under a different account).

---

## 7. Suggested Improvements

1. **Implement persona classification.** The keyword lists in `persona_specifications.json` are there — write a function that iterates over them and matches tokenized comment content to assign each user a persona. Pass `persona_rules` into the tokenizer or a new `classifier.py` module.
2. **Fix the tokenizer.** Assign the result of `nlp(text)` and use token-level features (lemmas, POS tags) to enrich the processed comment data before classifying.
3. **Add tests.** Start with unit tests for `reddit_text_cleaner.clean()` using hardcoded sample inputs and `tokenizer.tokenize()`. These require no network access and can be run with `pytest`.
4. **Document the persona rule format.** Add a section to the README explaining the structure of `persona_specifications.json`, including required fields and how to add new personas.
5. **Ensure both students' contributions are visible.** Make sure the second student commits code under their own GitHub account, or document how responsibilities were divided (e.g., in a `dev/` notes file or PR descriptions).
