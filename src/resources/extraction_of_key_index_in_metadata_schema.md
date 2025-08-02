## Extraction of Key Index in Metadata

You are given a JSON file containing metadata that follows a complex JSON Schema describing a dataset, its structure, and related contextual information.

### Your task is to:

1. Identify the subset of fields in the metadata that are most useful for generating data analysis code (e.g., Python with Pandas, R, SQL) that can load, explore, and process the dataset.

2. Your analysis should focus on fields that describe:

    - How to access the dataset (download links, file names, formats)

    - The structure of the dataset (table names, column names, data types, missing values)

    - Contextual metadata (title, abstract, keywords, geographic/temporal coverage)

    - Units and measurement details relevant to analysis.

### Input:

A JSON object representing metadata that follows the provided schema.

The metadata will include nested objects and arrays for dataset descriptions, access details, and structure.

#### Note:
 - We ingore spaitial data at current scope.
 - We need `additionalMetadata` for the definition of customized the variables and unites in the dataset.

### Output:
Return a JSON array of strings, each string being a dot-separated path to a field.

```json
[
  "dataset.dataTable[*].attributeList.attribute[*].attributeName.text",
  "dataset.dataTable[*].attributeList.attribute[*].storageType.text",
  "dataset.dataTable[*].physical.distribution.online.url.text"
]
```

The field path should be a dot-separated path (e.g., dataset.dataTable[*].attributeList.attribute[*].attributeName.text) and the description should explain how the field is useful for code generation.

Make sure the output is only a list of fields with descriptions — no explanations, no additional commentary.

### Constraints:
 - Output must be valid JSON.

 - Each path should be reusable for querying the JSON via JSONPath/JMESPath.

 - Do not include descriptions or extra text.

