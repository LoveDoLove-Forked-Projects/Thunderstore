# Digest-pinned: node 12 is EOL and deliberately frozen (it builds the legacy
# site's assets only). The pin stops the tag drifting or vanishing mid-migration.
FROM node:12-alpine@sha256:d4b15b3d48f42059a15bd659be60afe21762aae9d6cbea6f124440895c27db68

RUN mkdir -p /home/node/app/node_modules && mkdir /home/node/app/build && chown -R node:node /home/node/app
VOLUME /home/node/app/build
WORKDIR /home/node/app
COPY --chown=node:node ./builder/package.json ./builder/yarn.lock ./
USER node
RUN yarn install --frozen-lockfile
COPY --chown=node:node ./builder ./

ENTRYPOINT ["yarn", "run"]
CMD ["watch"]
