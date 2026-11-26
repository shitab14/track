# Frontend image (ADR0014): production Next.js build + start.
# NEXT_PUBLIC_API_URL is a build-time value baked into the client bundle.
FROM node:20-alpine

WORKDIR /app

# Install ALL dependencies (dev deps like TypeScript/Tailwind are needed to
# build). NODE_ENV is left unset here so npm ci does not skip devDependencies.
COPY package.json package-lock.json ./
RUN npm ci

# App source and the production build.
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Production mode for the running server only.
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "run", "start"]
