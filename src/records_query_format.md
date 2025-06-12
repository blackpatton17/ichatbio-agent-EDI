## PASTA+ Search Query Format (JSON-based)

This document defines how to construct a **JSON-based query format** for use by an LLM agent to interface with the PASTA+ (Environmental Data Initiative) EML search API. The format supports both full-text queries and exact filtering.

---

### 1. Endpoint

```
GET https://pasta.lternet.edu/package/search/eml
```

---

### 2. Field Categories

#### Single-Value Fields (used only in `fq`, exact or range match):

- `abstract`
- `begindate`
- `doi`
- `enddate`
- `funding`
- `geographicdescription`
- `id`
- `methods`
- `packageid`
- `pubdate`
- `responsibleParties`
- `scope`
- `singledate`
- `site`
- `taxonomic`
- `title`

#### Multi-Value Fields (can appear in `q` or as repeated `fq`):

- `author`
- `coordinates`
- `keyword`
- `organization`
- `projectTitle`
- `relatedProjectTitle`
- `timescale`

---

### 3. JSON Query Structure

```json
{
  "q": {
    "<field>": {
      "<term>": "existed | missing | prefix"
    }
  },
  "fq": {
    "<field>": {
      "type": "fulltext | exact | range",
      "value": "<filter_value>"
    }
  },
  "fl": ["<field1>", "<field2>", ...],
  "rows": 10
}
```

---

### 4. Query Semantics

#### `q`
- Specifies search intent per field.
- Values:
  - `existed`: term must be present
  - `missing`: term must be absent
  - `prefix`: term is used as a prefix search (e.g. `rain*`)

#### `fq`
- Filter queries that constrain results without affecting ranking.
- Structure includes:
  - `type`: one of `exact`, `fulltext`, or `range`
  - `value`: string or ISO 8601 range (e.g. `"[2010-01-01T00:00:00Z TO *]"`)

---

### 5. Example JSON Queries

**Example 1: Advanced keyword logic with scope filter**

```json
{
  "q": {
    "keyword": {
      "fire": "existed",
      "rainforest": "missing",
      "mash": "prefix"
    }
  },
  "fq": {
    "scope": {
      "type": "fulltext",
      "value": "edi"
    }
  },
  "fl": ["packageid", "doi", "keyword"],
  "rows": 10
}
```

**Example 2: Publication date range and organization filter**

```json
{
  "q": {
    "author": {
      "smith": "existed"
    }
  },
  "fq": {
    "pubdate": {
      "type": "range",
      "value": "[2015-01-01T00:00:00Z TO 2021-12-31T00:00:00Z]"
    },
    "organization": {
      "type": "exact",
      "value": "LTER"
    }
  },
  "fl": ["packageid", "title", "pubdate"]
}
```

---

### 6. Notes

- `q` terms can support flexible inclusion/exclusion logic per field.
- `fq` applies strict filtering — each condition must be met.
- Use `q={}` and rely on `fq` alone for filtering-only queries.
- The structure allows agents to reason explicitly about what to include, exclude, or prefix-match.
