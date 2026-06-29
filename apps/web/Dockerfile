# syntax=docker/dockerfile:1
FROM node:20-slim

ENV NODE_ENV=development
WORKDIR /app

# Install dependencies first for layer caching.
COPY package.json ./
RUN npm install

# Copy source.
COPY . .

EXPOSE 3000

# Dev server is sufficient for the infra skeleton; the full operator dashboard
# (production build) is delivered in MD 09.
CMD ["npm", "run", "dev"]
