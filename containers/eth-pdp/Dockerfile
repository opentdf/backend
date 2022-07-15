ARG NODE_VERSION=18-slim
# multi-stage build

# depender - get production dependencies
FROM node:${NODE_VERSION} as server
WORKDIR /app/
COPY package-lock.json .
COPY package.json .
RUN npm ci --no-audit
COPY .babelrc .
COPY index.js .
RUN npm run build
CMD node dist/index.js
