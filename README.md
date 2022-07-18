# USVISA-FR

Code is for personal, non-commercial use only

Disclaimer: This code is meant to facilitate scheduling meetings for the US embassy in Paris. It is not meant for abusing the appointment booking system. Please notice that you may get blocked for misusing the system. I take no responsibility for that.

Check and schedule visa appointments in the Paris embassy site.

This project is only specific to the US Paris embassy Non-Immigrant-Visas (several assumptions are made with that in mind), to use with other embassies may need some tweeks to work.

## Quickstart

(You will need `docker` and `docker-compose`)

- You need to have finished all the steps to ask for a visa in [https://ais.usvisa-info.com/en-fr/niv](https://ais.usvisa-info.com/en-fr/niv)
- You need to have one appointement already booked, even if it's in 2 years.
- Prepare a `.env` file with the following variables:
  - `USVISA_USERNAME`: Your email address.
  - `USVISA_PASSWORD`: Your password.
  (make sure to not share your credentials anywhere)

- Build the docker image: `docker-compose build`
- Start the docker image: `docker-compose up` or in detached mode: `docker-compose up -d`

The app will keep looking for new earlier appointements until it is stopped.

## Requirements

Locally:

- python3.10
- poetry

Docker:
* Docker
* docker-compose

## Usage

### Locally

- Install the dependencies: `poetry install`
- Prepare a `.env` file with the following variables:
  - `USVISA_USERNAME`: Your email address.
  - `USVISA_PASSWORD`: Your password.
  (make sure to not share your credentials anywhere)
- Start the app: `poetry run python main.py`

### Docker

- Build the docker image: `docker-compose build`
- Start the docker image: `docker-compose up` or in detached mode: `docker-compose up -d`
