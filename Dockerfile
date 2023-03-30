FROM cgr.dev/chainguard/python:3.11.2-dev@sha256:da9fe251d93cd4aec9febfac7d2ab78b9af986713bde9cadc135524ef6f84cb7 AS builder

COPY . /app

WORKDIR /app
RUN python -m pip install --no-cache-dir -r requirements.txt --require-hashes --no-warn-script-location;


FROM cgr.dev/chainguard/python:3.11.2@sha256:7a0724c1aa6d9a53b6719639a20fafdfe431ebe84fe0159519119c2b337ae455
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
