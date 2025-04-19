SHELL := /bin/bash
IMAGE := ghcr.io/1ndistinct/webscraper:latest

build:
	docker build \
	-f ./Dockerfile \
	--target production \
	-t ${IMAGE} \
	. 

debug:
	docker run -v ./webscraper:/app/webscraper -it ${IMAGE} bash

push: build
	docker push ${IMAGE}

test:
	coverage run -m pytest ./tests

run:
	python -m webscraper https://monzo.com

dockerrun: build
	docker run -it ${IMAGE} https://monzo.com

