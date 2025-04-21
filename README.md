# Web Scraper API

Given a starting URL, the crawler should visit each URL it finds on the same domain. It should print each URL visited, and a list of links found on that page. The crawler should be limited to one subdomain - so when you start with *https://monzo.com/*, it would crawl all pages on the monzo.com website, but not follow external links, for example to `facebook.com` or `community.monzo.com`.

## Extra information

1. Query params are left in the URL's and the same URL with differing query params will be scraped again. This is because the query params can influence how the page renders so theoretically more / differing links can appear with differing query params
2. URL's are only scraped once. so if they have been scraped before, they will not be scraped again.
3. Any URL which is ignored, or already scraped / in progress, will not be queued at all. this is more efficient.
4. fetching includes configurable retries and timeouts through environment variables.
5. It is assumed that all links are href's in the HTML. We are not considering links which are otherwise present in the html as raw text.
6. All links are validated to ensure correct formatting and prevent unexpected behaviour

## Install dependencies

1. [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
2. run `uv sync`
3. install precommit hooks `pre-commit install`
NOTE: If you are having issues, you may need to source the venv `source ./.venv/bin/activate`

## Testing

To run tests, either use the vscode testing extension or run `make test`. If you run `make test`, it will also show the test `coverage`.

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
