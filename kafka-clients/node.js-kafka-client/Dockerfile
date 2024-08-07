FROM node:20.8.0-alpine

# Create app directory
WORKDIR /app


# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY package*.json ./

RUN npm install
# If you are building your code for production
# RUN npm ci --only=production

# Bundle app source
COPY . .

# Copy .env file
#COPY .env ./

EXPOSE 3004
#CMD [ "node", "app.js" ]
#CMD ["npm", "run", "dev"]
CMD ["node", "src/app/app.js"]