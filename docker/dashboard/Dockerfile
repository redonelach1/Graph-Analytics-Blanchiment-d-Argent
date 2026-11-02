# =============================================================================
# Dashboard Container — Next.js 14+ with shadcn/ui & Tailwind CSS
# =============================================================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Install production dependencies
COPY dashboard/package*.json ./
RUN npm install --omit=dev

# Copy application source
COPY dashboard ./

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/api/health || exit 1

CMD ["npm", "run", "start"]
