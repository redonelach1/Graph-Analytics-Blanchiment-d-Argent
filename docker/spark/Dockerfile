# =============================================================================
# Spark Application Container
# Includes: PySpark + Delta Lake + GraphFrames + Kafka connector + confluent-kafka
# =============================================================================
FROM bitnamilegacy/spark:3.5.1

USER root

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------------------------
# Download JVM JARs — Delta Lake, GraphFrames, Kafka connector
# These are needed by Spark at runtime (not just pip packages)
# ---------------------------------------------------------------------------
ENV SPARK_JARS_DIR=/opt/bitnami/spark/jars

# Delta Lake 3.3.0 for Spark 3.5
RUN curl -fSL "https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.3.0/delta-spark_2.12-3.3.0.jar" \
    -o ${SPARK_JARS_DIR}/delta-spark_2.12-3.3.0.jar && \
    curl -fSL "https://repo1.maven.org/maven2/io/delta/delta-storage/3.3.0/delta-storage-3.3.0.jar" \
    -o ${SPARK_JARS_DIR}/delta-storage-3.3.0.jar
# Delta Lake 3.2.0 for Spark 3.5
RUN curl -fSL "https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.0/delta-spark_2.12-3.2.0.jar" \
    -o ${SPARK_JARS_DIR}/delta-spark_2.12-3.2.0.jar && \
    curl -fSL "https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.0/delta-storage-3.2.0.jar" \
    -o ${SPARK_JARS_DIR}/delta-storage-3.2.0.jar

# Spark Kafka connector
RUN curl -fSL "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar" \
    -o ${SPARK_JARS_DIR}/spark-sql-kafka-0-10_2.12-3.5.1.jar && \
    curl -fSL "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.1/kafka-clients-3.5.1.jar" \
    -o ${SPARK_JARS_DIR}/kafka-clients-3.5.1.jar && \
    curl -fSL "https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar" \
    -o ${SPARK_JARS_DIR}/spark-token-provider-kafka-0-10_2.12-3.5.1.jar && \
    curl -fSL "https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.12.0/commons-pool2-2.12.0.jar" \
    -o ${SPARK_JARS_DIR}/commons-pool2-2.12.0.jar

# GraphFrames 0.8.4 for Spark 3.5
RUN curl -fSL "https://repos.spark-packages.org/graphframes/graphframes/0.8.4-spark3.5-s_2.12/graphframes-0.8.4-spark3.5-s_2.12.jar" \
    -o ${SPARK_JARS_DIR}/graphframes-0.8.4-spark3.5-s_2.12.jar || \
    echo "WARNING: GraphFrames JAR download failed — try alternate source or manual install"

# ---------------------------------------------------------------------------
# Spark configuration defaults
# ---------------------------------------------------------------------------
ENV SPARK_HOME=/opt/bitnami/spark
COPY docker/spark/spark-defaults.conf ${SPARK_HOME}/conf/spark-defaults.conf

# ---------------------------------------------------------------------------
# Application code
# ---------------------------------------------------------------------------
WORKDIR /opt/app

USER 1001

