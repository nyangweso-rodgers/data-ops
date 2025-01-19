# Use the base image for MongoDB Community Server

# use latest image
#image: mongodb/mongodb-community-server:latest

#https://hub.docker.com/r/mongodb/mongodb-community-server  #mongodb-community-server
FROM mongodb/mongodb-community-server:7.0.7-ubi8 

# Set environment variables for MongoDB
ENV MONGODB_INITDB_ROOT_USERNAME=${MONGODB_INITDB_ROOT_USERNAME}
ENV MONGODB_INITDB_ROOT_PASSWORD=${MONGODB_INITDB_ROOT_PASSWORD}

# Set the default command to run MongoDB
CMD ["mongod", "--bind_ip_all"]