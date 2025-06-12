## PASTA+ Search Query Format (JSON-based)

This document defines how to construct a **JSON-based query format** for use by an LLM agent to interface with the PASTA+ (Environmental Data Initiative) EML search API. The format supports both full-text queries and exact filtering.

---

### 1. Endpoint

```
GET https://pasta.lternet.edu/package/search/eml
```

---

### 2. JSON Query Structure

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

### 3. Field Categories

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

### 4. Extended Field Types

#### Temporal Fields (subset of single-value fields)
- `begindate`
- `enddate`
- `singledate`
- `pubdate`

Use the following structure:
```json
"type": "range",
"value": {
  "gte": "YYYY-MM-DDTHH:MM:SSZ",
  "lte": "YYYY-MM-DDTHH:MM:SSZ"
}
```

#### Geographic Fields (subset of multi-value or single-value fields)
- `geographicdescription`
- `coordinates`
- `site`

**`coordinates` field example:**
```json
"coordinates": {
  "type": "range",
  "value": {
    "left_top": {
          "lat": <value>,
          "lon": <value>
        },
    "right_bottom": {
          "lat": <value>,
          "lon": <value>
        }
  }
}
```

Use `fulltext` for `geographicdescription`, and `prefix` for hierarchical names when applicable.

#### Taxonomic Fields
- `taxonomic`

Use `exact` for known taxa or `prefix` for genus/species patterns.

---

### 5. Query Semantics

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
  - `value`: either a string, a date range with `gte`/`lte`, or bounding box for coordinates

---

### 6. Example JSON Queries

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
      "value": {
        "gte": "2015-01-01T00:00:00Z",
        "lte": "2021-12-31T00:00:00Z"
      }
    },
    "organization": {
      "type": "exact",
      "value": "LTER"
    }
  },
  "fl": ["packageid", "title", "pubdate"]
}
```

**Example 3: Geographic and taxonomic filters**

```json
{
  "q": {},
  "fq": {
    "coordinates": {
      "type": "range",
      "value": {
        "left_top": {
          "lat": 45.0,
          "lon": -125.0
        },
        "right_bottom": {
          "lat": 40.0,
          "lon": -120.0
        },
      }
    },
    "taxonomic": {
      "type": "prefix",
      "value": "Quercus"
    }
  },
  "fl": ["packageid", "coordinates", "taxonomic"]
}
```

---

### 7. Notes

- `q` terms can support flexible inclusion/exclusion logic per field.
- `fq` applies strict filtering — each condition must be met.
- `fl` can include any valid field for response filtering.
- Use `gte`/`lte` format for date and numeric ranges.
- Use bounding box format for `coordinates` filtering.
