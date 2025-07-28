## PASTA+ Search Query Format (JSON-based)

This document defines how to construct a **JSON-based query format** for use by an LLM agent to interface with the PASTA+ (Environmental Data Initiative) EML search API. The format supports both full-text queries and exact filtering. The intention of this query is get to start with a research and a detailed record metadata analysis will be provided from another entrypoint.

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
  "fl": ["<field1>", "<field2>", ...]
}
```

---

### 3. Field Categories

#### Single-Value Fields (used only in `fq`, exact or range match):

- `abstract`
    - Required field.
- `title`
    - Required field.
- `begindate`
- `enddate`
- `funding`
- `geographicdescription`
- `methods` 
    - Note: don't use `methods` field except for use specifically asked so, since this will extremly increase the cost.
- `packageid`
    - Required field for simple summary,
- `doi`
- `pubdate`
- `responsibleParties`
- `scope`  
  - By default, if the user does not specify a scope, use `edi` in the query to indicate datasets submitted directly to EDI.  
  - For data belonging to a specific data collection site (e.g., Andrews Forest), use the corresponding `scope` value from the reference list at the end of this document.
- `singledate`
- `site`
- `taxonomic`

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
Note: User may enter some specific phrase in their request, so if they do so, substitute that phrase into the q filter.

**Example 1: Basic word searching**
Request: Show me the methods used in Meteorological data from the Discovery Tree at the Andrews Experimental Forest. 
```json
{
  "q": {
    "uncategorized": {
      "Meteorological": "existed",
      "Andrews Experimental": "existed",
      "Discovery Tree": "existed"
    }
  },
  "fq": {
    "scope": {
      "type": "fulltext",
      "value": "edi"
    }
  },
  "fl": ["*"]
}
```

**Example 2: Advanced keyword logic with scope filter**
Request: Show me datasets containing the keyword “fire,” missing the keyword “rainforest,” and where the keyword “mash” matches as a prefix.
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
  "fl": ["packageid", "doi", "keyword"]
}
```

**Example 3: Publication date range and organization filter**
Request: Find all datasets by the author “smith,” published between January 1, 2015 and December 31, 2021, from the LTER organization.
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

**Example 4: Geographic and taxonomic filters**
Request: Get all datasets for observations within a geographic box spanning latitudes 45.0 to 40.0 and longitudes -125.0 to -120.0 that involve taxa starting with “Quercus.”
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

## Available `scope` Site List

The following is a list of available `scope` values for use in queries, each pair is an available long term ecological research site:

- Andrews Forest LTER: `knb-lter-and`
- Arctic LTER: `knb-lter-arc`
- Baltimore Ecosystem Study LTER: `knb-lter-bes`
- Beaufort Lagoon Ecosystems LTER: `knb-lter-ble`
- Bonanza Creek LTER: `knb-lter-bnz`
- California Current Ecosystem LTER: `knb-lter-cce`
- Cedar Creek LTER: `knb-lter-cdr`
- Central Arizona–Phoenix LTER: `knb-lter-cap`
- City of Seattle (Urban Ecology): `knb-lter-cos`
- Coweeta LTER: `knb-lter-cwt`
- Florida Coastal Everglades LTER: `knb-lter-fce`
- Georgia Coastal Ecosystems LTER: `knb-lter-gce`
- Harvard Forest LTER: `knb-lter-hfr`
- Hubbard Brook LTER: `knb-lter-hbr`
- Jornada Basin LTER: `knb-lter-jrn`
- Kellogg Biological Station LTER: `knb-lter-kbs`
- Konza Prairie LTER: `knb-lter-knz`
- LTER Network Office: `knb-lter-nwk`
- Luquillo LTER: `knb-lter-luq`
- McMurdo Dry Valleys LTER: `knb-lter-mcm`
- Moorea Coral Reef LTER: `knb-lter-mcr`
- Minneapolis–St. Paul LTER: `knb-lter-msp`
- Niwot Ridge LTER: `knb-lter-nwt`
- North Inlet LTER: `knb-lter-nin`
- North Temperate Lakes LTER: `knb-lter-ntl`
- Northeast U.S. Shelf LTER: `knb-lter-nes`
- Northern Gulf of Alaska LTER: `knb-lter-nga`
- Palmer Antarctica LTER: `knb-lter-pal`
- Plum Island Ecosystems LTER: `knb-lter-pie`
- Santa Barbara Coastal LTER: `knb-lter-sbc`
- Sevilleta LTER: `knb-lter-sev`
- Shortgrass Steppe LTER: `knb-lter-sgs`
- Virginia Coast Reserve LTER: `knb-lter-vcr`

