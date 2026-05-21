FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /app
COPY ./cisco_network_rag/pom.xml ./cisco_network_rag/pom.xml
COPY ./cisco_network_rag/src ./cisco_network_rag/src
WORKDIR /app/cisco_network_rag
RUN mvn clean package -DskipTests

FROM tomcat:9.0-jdk17
RUN rm -rf /usr/local/tomcat/webapps/*
COPY --from=build /app/cisco_network_rag/target/cisco_network_rag.war /usr/local/tomcat/webapps/ROOT.war
EXPOSE 8080
CMD ["catalina.sh", "run"]