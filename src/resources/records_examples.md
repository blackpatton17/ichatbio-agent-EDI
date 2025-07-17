## PASTA+ JSON Query Examples

This document provides simple examples of JSON queries formatted for use with the PASTA+ EML search API. Each example demonstrates a specific type of filter or query logic to help guide development.

Note: unless the user delcare to search something in a specific field, e.g.  `keyword`, put the search clause term in `uncategorized` field to allow a non-strict search. However, there is no `uncategorized` allowed in the `fq` field allowed yet.

---

### Example 1: Basic search in EDI scope
```json
{
  "q": {
    "uncategorized": {
      "Castor canadensis": "existed"
    }
  },
  "fq": {
    "scope": {
      "type": "exact",
      "value": "edi"
    }
  },
  "fl": ["packageid", "keyword"],
  "rows": 50
}
```

### Example 2: Keyword match and scope filter
```json
{
  "q": {
    "keyword": {
      "plant": "existed"
    }
  },
  "fq": {
    "scope": {
      "type": "exact",
      "value": "edi"
    }
  },
  "fl": ["packageid", "keyword"],
  "rows": 50
}
```

### Example 3: Missing keyword and prefix match
```json
{
  "q": {
    "keyword": {
      "carbon": "missing",
      "eco": "prefix"
    }
  },
  "fl": ["packageid", "keyword"],
  "rows": 50
}
```

### Example 4: Author presence and date range
```json
{
  "q": {
    "author": {
      "jones": "existed"
    }
  },
  "fq": {
    "pubdate": {
      "type": "range",
      "value": {
        "gte": "2010-01-01T00:00:00Z",
        "lte": "2020-12-31T00:00:00Z"
      }
    }
  },
  "fl": ["packageid", "author", "pubdate"],
  "rows": 50
}
```

### Example 5: Coordinate bounding box
```json
{
  "q": {},
  "fq": {
    "coordinates": {
      "type": "range",
      "value": {
        "left_top": {"lat": 47.0, "lon": -125.0},
        "right_bottom": {"lat": 42.0, "lon": -120.0}
      }
    }
  },
  "fl": ["packageid", "coordinates"],
  "rows": 5
}
```

### Example 6: Taxonomic and geographic description prefix
```json
{
  "q": {
    "geographicdescription": {
      "type": "existed",
      "value": "Olympic"
    }
  },
  "fq": {
    "taxonomic": {
      "type": "prefix",
      "value": "Acer"
    }
  },
  "fl": ["packageid", "taxonomic", "geographicdescription"],
  "rows": 8
}
```

---

Each example can be modified or extended by combining filters or adding more fields to the `fl` (field list).
