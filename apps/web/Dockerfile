FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Next.js inlines NEXT_PUBLIC_* vars into the client bundle at build time,
# so this must be a build ARG, not a runtime `environment:` entry in compose.
ARG NEXT_PUBLIC_CORE_API_BASE_URL
ENV NEXT_PUBLIC_CORE_API_BASE_URL=$NEXT_PUBLIC_CORE_API_BASE_URL
RUN npm run build && npm prune --omit=dev
ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

CMD ["npm", "start"]
