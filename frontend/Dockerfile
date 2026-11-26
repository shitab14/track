# Frontend image (ADR0014): production Next.js build + start.
# NEXT_PUBLIC_API_URL is a build-time value baked into the client bundle.
FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

# Install dependencies (incl. dev deps needed to build) with layer caching.
COPY package.json package-lock.json ./
RUN npm ci

# App source and the production build.
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
