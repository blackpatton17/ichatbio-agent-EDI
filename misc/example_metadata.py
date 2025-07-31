import requests
import json
from genson import SchemaBuilder

# Step 1: Download the JSON data
url = "http://34.219.182.153:9000/ichatbio-edi-agent-artifact-test/edi/1262/2/metadata.json"
response = requests.get(url)
response.raise_for_status()
data = response.json()

# Step 2: Generate the schema
builder = SchemaBuilder()
builder.add_object(data)
schema = builder.to_schema()

# Step 3: Save the schema to a file
with open("metadata_schema.json", "w") as f:
    json.dump(schema, f, indent=2)

print("Schema saved as metadata_schema.json")