FROM node:alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Generate the Prisma Client
RUN npx prisma generate

# Expose port
EXPOSE 3005

# Start the application (replace 'node app.js' if your entry point differs)
#CMD ["npm", "run", "dev"]
CMD [ "node", "app.js" ]