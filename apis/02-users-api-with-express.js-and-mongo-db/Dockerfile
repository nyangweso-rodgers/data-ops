FROM node:alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose port
EXPOSE 3002

# Start the application (replace 'node app.js' if your entry point differs)
#CMD ["npm", "run", "dev"]
CMD [ "node", "app.js" ]