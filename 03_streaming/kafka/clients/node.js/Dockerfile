#FROM node:20.8.0-alpine
#FROM node:latest
FROM node:20.17.0-alpine3.20 

# Install Python
#RUN apk add --no-cache python3 make g++ bash

# Create app directory
WORKDIR /app

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY package*.json ./

RUN npm install

# Bundle app source
COPY . .

# Copy .env file
COPY .env ./

EXPOSE 3004

CMD [ "node", "app.js" ]
#CMD ["npm", "run", "dev"]