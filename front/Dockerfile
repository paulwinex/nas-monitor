# Build stage
FROM node:20-slim AS build-stage

WORKDIR /app

# Install global quasar cli
RUN npm install -g @quasar/cli

# Copy package and config files
COPY package.json yarn.lock* package-lock.json* quasar.config.* jsconfig.json* tsconfig.json* index.html ./

# Install dependencies 
RUN npm install

# Copy source code
COPY . .

# Build for production
# You can pass VITE_API_BASE at build time
ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE

RUN quasar build

# Final stage
FROM nginx:stable-alpine AS production-stage

RUN rm -rf /usr/share/nginx/html/*
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
