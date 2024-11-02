# SPARA

This is a cumulative repository for SPARA - chatbot for energy efficiency in buildings. It includes the following components:

- **server** - Python Flask based web server
- **client** - React JS based client

To fetch the project codebase to the local machine, the following should be done:

```
git clone git@github.com:KTH-UrbanT/spara.git
git clone --recursive git@github.com:KTH-UrbanT/spara.git
```

## Composing the Docker

### Development

Build and run the development environment:

```
docker-compose up --build
```

### Production

Build and run the production environment:

```
docker-compose -f docker-compose.prod.yml up --build -d
```
