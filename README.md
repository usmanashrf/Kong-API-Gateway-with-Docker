# Docker Compose Services and Integration with Kong API Gateway

## Services in Docker Compose File

The provided `docker-compose.yml` file sets up multiple services. Here is a detailed explanation of each service:

- **Kong Migrations**:
  - `kong-migrations`: Initializes the database by running Kong's migrations.
  - `kong-migrations-up`: Runs any new migrations to update the database schema.

- **Kong**:
  - The main Kong API Gateway service. It listens on port 8000 for proxying requests, 8001 for the Admin API, and 8002 for the Admin GUI.

- **PostgreSQL Database**:
  - `db`: The PostgreSQL database used by Kong for storing configuration and other data.

- **User Data Service**:
  - `user-data-service`: A custom service you have built that listens on port 8005.

- **Read Data Service**:
  - `read-data-service`: Another custom service that listens on port 8008.

## Docker Compose File Explanation

```yaml
version: '3.9'

x-kong-config:
  &kong-env
  KONG_DATABASE: ${KONG_DATABASE:-postgres}
  KONG_PG_DATABASE: ${KONG_PG_DATABASE:-kong}
  KONG_PG_HOST: db
  KONG_PG_USER: ${KONG_PG_USER:-kong}
  KONG_PG_PASSWORD_FILE: /run/secrets/kong_postgres_password

volumes:
  kong_data: {}
  kong_prefix_vol:
    driver_opts:
      type: tmpfs
      device: tmpfs
  kong_tmp_vol:
    driver_opts:
      type: tmpfs
      device: tmpfs

networks:
  default:
    driver: bridge

services:
  kong-migrations:
    image: "${KONG_DOCKER_TAG:-kong:latest}"
    command: kong migrations bootstrap
    profiles: [ "database" ]
    depends_on:
      - db
    environment:
      <<: *kong-env
    secrets:
      - kong_postgres_password
    restart: on-failure

  kong-migrations-up:
    image: "${KONG_DOCKER_TAG:-kong:latest}"
    command: kong migrations up && kong migrations finish
    profiles: [ "database" ]
    depends_on:
      - db
    environment:
      <<: *kong-env
    secrets:
      - kong_postgres_password
    restart: on-failure

  kong:
    image: "${KONG_DOCKER_TAG:-kong:latest}"
    user: "${KONG_USER:-kong}"
    environment:
      <<: *kong-env
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_PROXY_LISTEN: "${KONG_PROXY_LISTEN:-0.0.0.0:8000}"
      KONG_ADMIN_LISTEN: "${KONG_ADMIN_LISTEN:-0.0.0.0:8001}"
      KONG_ADMIN_GUI_LISTEN: "${KONG_ADMIN_GUI_LISTEN:-0.0.0.0:8002}"
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_PREFIX: ${KONG_PREFIX:-/var/run/kong}
      KONG_DECLARATIVE_CONFIG: "/opt/kong/kong.yaml"
    secrets:
      - kong_postgres_password
    ports:
      # The following two environment variables default to an insecure value (0.0.0.0)
      # according to the CIS Security test.
      - "${KONG_INBOUND_PROXY_LISTEN:-0.0.0.0}:8000:8000/tcp"
      - "${KONG_INBOUND_SSL_PROXY_LISTEN:-0.0.0.0}:8443:8443/tcp"
      # Making them mandatory but undefined, like so would be backwards-breaking:
      # - "${KONG_INBOUND_PROXY_LISTEN?Missing inbound proxy host}:8000:8000/tcp"
      # - "${KONG_INBOUND_SSL_PROXY_LISTEN?Missing inbound proxy ssl host}:8443:8443/tcp"
      # Alternative is deactivating check 5.13 in the security bench, if we consider Kong's own config to be enough security here

      - "127.0.0.1:8001:8001/tcp"
      - "127.0.0.1:8444:8444/tcp"
      - "127.0.0.1:8002:8002/tcp"
    healthcheck:
      test: [ "CMD", "kong", "health" ]
      interval: 10s
      timeout: 10s
      retries: 10
    restart: on-failure:5
    read_only: true
    volumes:
      - kong_prefix_vol:${KONG_PREFIX:-/var/run/kong}
      - kong_tmp_vol:/tmp
      # - ./config:/opt/kong
    security_opt:
      - no-new-privileges

  db:
    image: postgres:9.5
    profiles: [ "database" ]
    environment:
      POSTGRES_DB: ${KONG_PG_DATABASE:-kong}
      POSTGRES_USER: ${KONG_PG_USER:-kong}
      POSTGRES_PASSWORD_FILE: /run/secrets/kong_postgres_password
    secrets:
      - kong_postgres_password
    healthcheck:
      test:
        [
          "CMD",
          "pg_isready",
          "-d",
          "${KONG_PG_DATABASE:-kong}",
          "-U",
          "${KONG_PG_USER:-kong}"
        ]
      interval: 30s
      timeout: 30s
      retries: 3
    restart: on-failure
    stdin_open: true
    tty: true
    volumes:
      - kong_data:/var/lib/postgresql/data

  user-data-service:
    build: ./user_data_service
    ports:
      - "8005:8005"
  
  read-data-service:
    build: ./read_data_service
    ports:
      - "8008:8008"
secrets:
  kong_postgres_password:
    file: ./POSTGRES_PASSWORD
```


## Step-by-Step Guide

1. **Start Kong and PostgreSQL**:
   - Ensure Docker is running.
   - Start Kong and PostgreSQL using Docker Compose:
     ```bash
     docker-compose --profile database up -d
     ```
2. **Access Kong Admin GUI**:
   - Open your web browser and go to [http://localhost:8002](http://localhost:8002).
   - Login to the Kong Admin GUI.

3. **Create a Gateway Service**:
   - Navigate to the **Gateway Services** section.
   - Click on **Add Service**.
   - Enter the service details (name, URL).
   - Click **Save**.
     
4. **Create a Route**:
   - Navigate to the **Routes** section.
   - Click on **Add Route**.
   - Configure the route (service, path).
   - Click **Save**.

5. **Create a Consumer** (Optional):
   - Go to the **Consumers** section.
   - Click on **Add Consumer**.
   - Enter consumer details (username).
   - Click **Save**.
     
6. **Enable the JWT Plugin**:
   - Go to the **Plugins** section.
   - Click on **Add Plugin**.
   - Select the **JWT** plugin.
   - Configure the plugin (secret key, issuer claim name).
   - Click **Save**.
  
7. **Create JWT Credentials** (from postman):
   - make a post call to [http://localhost:8001/consumers/<consumer>/jwt]
   - The request will return the response like this:

  ```json
  {
    "algorithm": "HS256",
    "consumer": {
      "id": "789955d4-7cbf-469a-bb64-8cd00bd0f0db"
    },
    "created_at": 1652208453,
    "id": "95d4ee08-c68c-4b69-aa18-e6efad3a4ff0",
    "key": "H8WBDhQlcfjoFmIiYymmkRm1y0A2c5WU",
    "rsa_public_key": null,
    "secret": "n415M6OrVnR4Dr1gyErpta0wSKQ2cMzK",
    "tags": null
  }
```
  - In response secret will use to generate your Jwt token

8. **Create JWT token from fastapi**
   - Install following dependencied fastapi, sqlmodel, jwt, httpx
   - past the below code in your file
```python
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI
from sqlmodel import SQLModel
from typing import Optional
import jwt
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("read data services started")
    yield
    
app = FastAPI(lifespan = lifespan, title="read data services")

class TokenData(SQLModel):
    iss: str


SECRET_KEY = "n415M6OrVnR4Dr1gyErpta0wSKQ2cMzK"   # past your secret key here which you get in step 7, in our case we have "n415M6OrVnR4Dr1gyErpta0wSKQ2cMzK"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600


def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = min(expire, datetime(2038, 1, 19, 3, 14, 7))  # Limit expiration time to 2038-01-19 03:14:07 UTC
    to_encode.update({"exp": expire})
    headers = {
        "typ": "JWT",
        "alg": ALGORITHM
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM, headers=headers)
    return encoded_jwt


@app.post("/generate-token/")
def generate_token(data: TokenData):
    payload = {"iss": data.iss}
    token = create_jwt_token(payload)
    return {"token": token}
```

9. **Test the Setup**:
   - Use tools like Postman to test your setup.
   - Generate a JWT token (if needed) and include it in the `Authorization` header of your requests.
   - Send requests to your service's endpoint through Kong.
   - In our case it http://localhost:8000/user
   - ```curl --location 'http://localhost:8000/user' \ --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCjsakaksdkabsdkabkdgkfdjkdVNTdiIsImV4cCI6MTcxNjYzODkwNn0.iumF4Tk0BOBZh0kfoff8t-SbL65Ryk7mVyNCWC_KDQE'```

