docker build -f .dockerfile -t blackpatton17/ichatbio-agent-edi:latest --no-cache .
docker buildx build --platform linux/amd64 -f .dockerfile -t blackpatton17/ichatbio-agent-edi:latest --no-cache --push .
docker push blackpatton17/ichatbio-agent-edi:latest



docker pull blackpatton17/ichatbio-agent-edi && docker logs -f $(docker run --rm -it -d \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    -e S3_ENDPOINT=$S3_ENDPOINT \
    -e S3_BUCKET=$S3_BUCKET \
    -e S3_ACCESS_KEY=$S3_ACCESS_KEY \
    -e S3_SECRET_KEY=$S3_SECRET_KEY \
    -p 8000:8000 blackpatton17/ichatbio-agent-edi)