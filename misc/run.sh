docker build -f .dockerfile -t blackpatton17/ichatbio-agent-edi:latest --no-cache .
docker buildx build --platform linux/amd64 -f .dockerfile -t blackpatton17/ichatbio-agent-edi:latest --no-cache --push .
docker push blackpatton17/ichatbio-agent-edi:latest
docker run --rm -it -d -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8000:8000 blackpatton17/ichatbio-agent-edi
