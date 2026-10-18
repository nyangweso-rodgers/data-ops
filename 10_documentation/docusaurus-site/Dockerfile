# 10_documentation/docusaurus-site/Dockerfile
# One image for both environments:
#   dev  - `npm start` (hot-reload dev server; source mounted by docker-compose-docusaurus.dev.yml)
#   prod - `npm run build` at image build time, served by `npm run serve` (see prod.yml)
FROM node:20-alpine

WORKDIR /app

# Install dependencies first so they're cached across source changes
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN chown -R node:node /app

USER node
EXPOSE 3000

CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "3000"]
