FROM node:alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Generate the Prisma Client
#RUN npx prisma generate

# init prisma
RUN npx prisma generate --schema=./prisma/schema.prisma

# Expose port
EXPOSE 3002

CMD ["npm", "run", "dev"]