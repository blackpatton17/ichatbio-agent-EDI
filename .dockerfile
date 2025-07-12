# Based on https://github.com/docker/awesome-compose/blob/18f59bdb09ecf520dd5758fbf90dec314baec545/nginx-wsgi-flask/flask/Dockerfile

FROM python:3.12-bullseye

RUN apt-get update -y\
 && apt-get install -y\
      python3-pip \
      curl

# Permissions and nonroot user for tightened security
RUN adduser --disabled-password nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
WORKDIR /home/app
USER nonroot

# Copy files to the container
COPY --chown=nonroot:nonroot . .


# Python setup
# RUN python3 -m venv .venv
# RUN .venv/bin/activate && pip install -r requirements.txt
RUN pip3 install -r requirements.txt

# Define the port number the container should expose
EXPOSE 8000


CMD ["python3", "src"]