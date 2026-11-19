# =============================================================================
# Dashboard Container — Next.js 14+ with shadcn/ui & Tailwind CSS
# =============================================================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Install all dependencies (devDependencies needed for build: tailwind, typescript, etc.)
COPY dashboard/package*.json ./
RUN npm install --include=dev

# Copy application source
COPY dashboard ./

# Build production Next.js application
RUN npm run build

# Set production environment for runtime
ENV NODE_ENV=production

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/api/health || exit 1

CMD ["npm", "run", "start"]
