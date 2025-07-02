@override
async def run(self, request: str, entrypoint: str, params: Optional[BaseModel]):
    async with context.begin_process(summary="Generating EDI query") as process:
        simple_params, description = await _generate_records_search_parameters(request)
        edi_query = EDIQueryModel(**simple_params.model_dump())
        url = edi_query.to_url()

        await process.log(f"Using structured parameters to query EDI, url: {url}")

        await process.log(f"Sending GET request to {url}")
        response = await self._fetch_edi_data(url)

        if response.status_code != 200:
            raise AIGenerationException(f"Failed to fetch data from EDI: {response.status_code} {response.text}")
            return
        results = response.text.strip()
        
        if not results:
            await process.log("No datasets matched your query.")
            return
        
        await process.log("Datasets found, processing results...")
        root = ET.fromstring(results)
        entries = []
        for doc in root.findall("document")[:10]:
            entry = {}
            for child in doc:
                # If the child has sub-elements, handle as list or dict
                if list(child):
                    # If all sub-elements are <keyword>, collect as list
                    if all(grandchild.tag == "keyword" for grandchild in child):
                        entry[child.tag] = [kw.text for kw in child.findall("keyword")]
                    else:
                        # For other nested structures, store as dict
                        entry[child.tag] = {grandchild.tag: grandchild.text for grandchild in child}
                else:
                    entry[child.tag] = child.text
            # Add a URL field if packageid exists
            if "packageid" in entry:
                # Convert packageid from "scope.id.revision" to "scope/id/revision"
                scope, id_, revision = entry["packageid"].split(".")
                entry["url"] = f"https://pasta.lternet.edu/package/metadata/eml/{scope}/{id_}/{revision}"
            entries.append(entry)

        await context.reply(
            "Results saved locally"
            # description=f"Saved the top 10 datasets to {output_path.resolve()}",
            # data={"output_path": str(output_path.resolve())}
        )

        await process.create_artifact(
            mimetype="application/json",
            description=f"Here are the top 10 matching datasets from {url}",
            content=json.dumps({"datasets": entries}).encode("utf-8")
        )
        # Save the entries to a local JSON file
        # output_path = Path(os.getenv("EDI_RESULTS_PATH", "edi_search_results.json"))
        # with output_path.open("w", encoding="utf-8") as f:
        #     json.dump({"datasets": entries}, f, ensure_ascii=False, indent=2)
