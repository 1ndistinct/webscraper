# Web Scraper API

Given a starting URL, the crawler should visit each URL it finds on the same domain. It should print each URL visited, and a list of links found on that page. The crawler should be limited to one subdomain - so when you start with *https://monzo.com/*, it would crawl all pages on the monzo.com website, but not follow external links, for example to `facebook.com` or `community.monzo.com`.

## Install dependencies

1. [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
2. run `uv sync`
3. install precommit hooks `pre-commit install`
NOTE: If you are having issues, you may need to source the venv `source ./.venv/bin/activate`

## Testing

To run tests, either use the vscode testing extension or run `make test`

## Running the App

The app can be run:
1. Using the vscode launch config ( `./.vscode/launch.json` ) and clicking the play button on `Python: Scraper Entrypoint` in the `RUN AND DEBUG` tab in vscode
2. run `python -m webscraper <http_url>` or `make run`
3. run in docker with `make dockerrun`

#### NOTE: For help in how to run the application, do python -m webscraper --help

## Building the image

1. run `make build`

## Deployment

This application can be deployed in any containerised environment. Options are. First thing to do is push the image with `make push` assuming you are already authenticated with the container registry.

1. Docker / Docker Swarm
2. Kubernetes
3. ECS or equivalent

## Linting

1. Run the precommit hooks with `pre-commit run --all-files`
