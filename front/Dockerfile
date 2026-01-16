# Build stage
FROM node:20-slim AS build-stage

WORKDIR /app

# Install global quasar cli
RUN npm install -g @quasar/cli

# Copy package files
COPY package.json yarn.lock* package-lock.json* ./

# Install dependencies 
# Using npm install because yarn is available but maybe not configured in the environment
RUN npm install

# Copy source code
COPY . .

# Build for production
# You can pass VITE_API_BASE at build time
ARG VITE_API_BASE=http://localhost:8000
ENV VITE_API_BASE=$VITE_API_BASE

RUN quasar build

# Final stage
FROM nginx:stable-alpine AS production-stage

# Copy custom nginx config if needed, or use default
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build files from build-stage
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
