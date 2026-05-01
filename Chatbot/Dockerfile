FROM rasa/rasa:3.6.20-full

WORKDIR /app

COPY config.yml .
COPY domain.yml .
COPY credentials.yml .
COPY data/ data/

# Production endpoints: action server at Docker service name
COPY endpoints.docker.yml endpoints.yml

# Models are mounted as a volume in docker-compose,
# but copy any pre-trained models as fallback
COPY models/ models/

USER root
RUN chown -R 1001:1001 /app
USER 1001

EXPOSE 5005

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5005/status || exit 1

CMD ["run", "--enable-api", "--cors", "*", "--port", "5005"]
