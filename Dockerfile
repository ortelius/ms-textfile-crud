FROM cgr.dev/chainguard/python:3.11.2-dev@sha256:ff6601961d77379c14a08a01a96709f772d603d0aacd5163da123fb7232b9f6d AS builder

COPY . /app

WORKDIR /app
RUN python -m pip install --no-cache-dir -r requirements.txt --require-hashes --no-warn-script-location;


FROM cgr.dev/chainguard/python:3.11.2@sha256:ac3f51e461da51aacd40654e796e0901fad88e0e0c396f4d79b806119427fc67
USER nonroot
ENV DB_HOST localhost
ENV DB_NAME postgres
ENV DB_USER postgres
ENV DB_PASS postgres
ENV DB_PORT 5432

COPY --from=builder /app /app
COPY --from=builder /home/nonroot/.local /home/nonroot/.local

WORKDIR /app

EXPOSE 8080
ENV PATH=$PATH:/home/nonroot/.local/bin

HEALTHCHECK CMD curl --fail http://localhost:8080/health || exit 1

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
