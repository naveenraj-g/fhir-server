# Builds HL7/Inferno's fhir-validator-wrapper — a REST wrapper around the
# official HL7 Java FHIR validator — as a standalone sidecar.
#
# Why this exists: a stopgap for full StructureDefinition/profile validation
# (including snapshot generation across a base -> country -> organization
# profile chain) until this project's own validation engine is built — see
# docs/architecture/fhir-profiling-and-extensibility-strategy.md and
# docs/structure-definitions/12-three-layer-validation-architecture.md.
# Swapping it out later means replacing whichever thin Python client calls
# this container's REST API, not anything about how profiles are stored.
#
# Source: https://github.com/inferno-framework/fhir-validator-wrapper
# REST API: https://github.com/inferno-framework/fhir-validator-wrapper/blob/main/rest-api.md
#   POST /profiles            register a StructureDefinition (base/country/org
#                             layers, read from this project's own DB, converted
#                             to true FHIR JSON, then POSTed here)
#   POST /validate?profile=<url>   validate a resource against a registered
#                                   profile (the validator walks baseDefinition
#                                   chains among whatever's already registered)
#   POST /evaluate?path=<FHIRPath> evaluate a FHIRPath expression — usable as a
#                                   stopgap for org-1/org-2/org-3 and any custom
#                                   invariant's constraint.expression
#
# Pinned to a specific upstream release tag for reproducibility — this
# Dockerfile deliberately does not track their default branch.
ARG VALIDATOR_WRAPPER_REF=v2.3.6

# Using the official `gradle` image (which bundles Gradle itself) for the
# build stage, and invoking `gradle` directly instead of `./gradlew build` —
# the wrapper script insists on downloading its own pinned Gradle
# distribution from services.gradle.org at build time, which timed out
# repeatedly from inside Docker's build sandbox on this machine even though
# the host itself can reach that host fine. Version pinned to exactly what
# the project's own gradle-wrapper.properties specifies (7.2), so this isn't
# a behavioral change, just a different way of getting the same Gradle onto
# disk.
FROM gradle:7.2.0-jdk11 AS build
ARG VALIDATOR_WRAPPER_REF
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
# Clone into a fresh subdirectory, not WORKDIR itself — /home isn't
# guaranteed empty on every base image, and `git clone ... .` refuses to run
# into a non-empty directory.
RUN git clone --branch ${VALIDATOR_WRAPPER_REF} --depth 1 \
      https://github.com/inferno-framework/fhir-validator-wrapper.git /home/src
WORKDIR /home/src
RUN gradle build --no-daemon
RUN tar -xf build/distributions/InfernoValidationService-*.tar

FROM eclipse-temurin:11-jre
WORKDIR /home
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75.0"
# curl only: lets docker-compose's healthcheck hit GET /version without
# needing a separate tool installed on the host.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /home/src/InfernoValidationService-* .
RUN ./bin/InfernoValidationService prepare
EXPOSE 4567
CMD ["./bin/InfernoValidationService"]
