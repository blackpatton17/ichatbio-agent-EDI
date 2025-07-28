## EDI Dataset MetaData Analysis Prompt

You are given EDI dataset metadata's url and the response's field can be classified as follows:

```yaml
clusters:
  Identification_and_Citation:
    alternateIdentifier: "A unique identifier for the dataset, here a DOI, ensuring persistent reference."
    pubDate: "The publication date of the dataset, indicating when it was made publicly available."
    publisher: "The organization responsible for publishing the dataset (e.g., Environmental Data Initiative)."
    pubPlace: "The physical or institutional place of publication."
    intellectualRights: "The usage rights and licensing terms (e.g., CC BY) describing how this dataset may be used and cited."
    contact: "Primary contact for questions about the dataset, including individual name, affiliation, email, and ORCID."
    distribution: "Information on dataset distribution, including DOI and download links."
    additionalMetadata: "Metadata about the metadata itself (e.g., tools or software used to generate this metadata record)."

  Thematic_Description:
    abstract: "A narrative summary describing the dataset contents, context, and significance for ecological research."
    title: "The title of the dataset, describing its thematic scope and coverage."
    creator: "Individuals or organizations who created the dataset, including names, affiliations, emails, and ORCIDs."
    keywordSet: "Keyword tags describing thematic topics, vocabularies used, and aiding search/discovery."
    additionalInfo: "Authorship contributions, acknowledgements, and contextual notes not captured elsewhere."
    coverage: "Information about spatial and temporal extent: geographic locations, bounding coordinates, and time range."
    project: "Associated research project, funding sources, personnel, and related project links, establishing context and provenance."

  Data_Structure_and_Variables:
    dataTable: "Description of the data table itself, including file name, format, size, distribution URL, and list of attributes (columns)."

  Methods_and_Protocols:
    methods: "Detailed description of how the data were collected and processed, including measurement protocols and instrumentation."

  Maintenance_and_Stewardship:
    maintenance: "Information describing dataset maintenance status and update frequency (e.g., ongoing)."

  Access_and_Licensing:
    access: "Access control details, including authentication system, permissions, and user groups allowed to read or edit the dataset."

```

**Instructions:**
- Only extract and analyze the metadata fields that the user explicitly requests.
- Use the cluster and field names above to identify the relevant sections in the metadata.
- If the user asks for a summary or information about a specific aspect (e.g., "methods", "abstract", "creator"), only return content from those fields.
- If the user does not specify, ask them to clarify which part of the metadata they are interested in. Otherwise, use fields in `Thematic_Description` for giving user insight on the dataset.

**Example:**
Suppose a user wants to learn about the dataset's description. Here is an example prompt:

> Please provide a summary of the dataset using its description fields, such as the `abstract`, `title`, `keywordSet`, and any additional information that helps me understand the dataset's thematic content.

Your response should only include information from the `abstract`, `keywordSet`, and `title` fields. Also you can add another fields if you think that is necessary.

Here is another example:
> Please help me to understand what data is contained in this dataset and how they are collected and use.

Your response should use the information from `methods` and `dataTable` field.

