# Containerfile for av-be's staged Play Framework runtime.
FROM eclipse-temurin:11-jre-jammy

RUN apt-get update && apt-get install -y --no-install-recommends bash curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY target/universal/stage /app

EXPOSE 9000

ENTRYPOINT ["/app/bin/av"]
CMD ["-Dplay.server.pidfile.path=/dev/null"]
