## [1.1.0](https://github.com/GezzyDax/marzban-telegram-bot/compare/v1.0.4...v1.1.0) (2025-10-05)

### Features

* add 'About Bot' button to admin menu ([5d88743](https://github.com/GezzyDax/marzban-telegram-bot/commit/5d88743b1501462d036a76d33b2736d625217cd1))

## [1.0.4](https://github.com/GezzyDax/marzban-telegram-bot/compare/v1.0.3...v1.0.4) (2025-10-05)

### Bug Fixes

* auto-populate inbounds when creating Marzban users ([f0da3b2](https://github.com/GezzyDax/marzban-telegram-bot/commit/f0da3b2fca82dfbe4fc2ecd675391e4497c2f2b9))

## [1.0.3](https://github.com/GezzyDax/marzban-telegram-bot/compare/v1.0.2...v1.0.3) (2025-10-04)

### Bug Fixes

* set semantic-release job outputs for GitOps update ([12ba884](https://github.com/GezzyDax/marzban-telegram-bot/commit/12ba8843302fcccb05db814a9f1cb04bb892b36d))

## [1.0.2](https://github.com/GezzyDax/marzban-telegram-bot/compare/v1.0.1...v1.0.2) (2025-10-04)

### Bug Fixes

* improve smoke test to handle Telegram token validation ([92fcd8f](https://github.com/GezzyDax/marzban-telegram-bot/commit/92fcd8fa58d00baf34ff586e3f31fc25c131619d))

## [1.0.1](https://github.com/GezzyDax/marzban-telegram-bot/compare/v1.0.0...v1.0.1) (2025-10-04)

### Bug Fixes

* correct GitOps values file path and tag format ([7682d82](https://github.com/GezzyDax/marzban-telegram-bot/commit/7682d82b9ec554a9796e585698565a7dd5878b2d))
* smoke test database connection in CI/CD ([df75561](https://github.com/GezzyDax/marzban-telegram-bot/commit/df75561a5c240ce3847c820bdc2df44dbb5b125d))

## 1.0.0 (2025-10-04)

### Features

* add bot version display in admin panel ([ef4f33f](https://github.com/GezzyDax/marzban-telegram-bot/commit/ef4f33fc50c3a6cbe2378d2bc13dca17a6800348))
* add modify_user method to MarzbanAPI ([c9722b4](https://github.com/GezzyDax/marzban-telegram-bot/commit/c9722b40eb04eb76392b8852fad59f8964992284))
* add ToggleUserStatusStates FSM ([c618e9b](https://github.com/GezzyDax/marzban-telegram-bot/commit/c618e9b632eef1e570477554f08b82a9c89aa7a1))
* implement user status toggle with confirmation ([2e14dd1](https://github.com/GezzyDax/marzban-telegram-bot/commit/2e14dd13e9457205fb0c7098882c642949436bb3))
* migrate CI/CD to GitHub Actions with Harbor registry ([c70f4e2](https://github.com/GezzyDax/marzban-telegram-bot/commit/c70f4e29ba1ebb02aea7d8bd1e7e01ddcd7d0026))
* support multiple telegram bindings ([cb2cf99](https://github.com/GezzyDax/marzban-telegram-bot/commit/cb2cf99ba4d46d8e72924a10038cf3c0d1138349))

### Bug Fixes

* allow multiple telegram bindings in legacy admin flows ([6af5bf5](https://github.com/GezzyDax/marzban-telegram-bot/commit/6af5bf57ac72e5ff802890e7c11d361b721b4ca7))
* copy Alembic migrations to Docker image ([557c1de](https://github.com/GezzyDax/marzban-telegram-bot/commit/557c1de60adf030d981635569231d918647b3b5b))
* correct Python packages PATH for non-root user ([77fba5e](https://github.com/GezzyDax/marzban-telegram-bot/commit/77fba5ecd764d38ef00fc8cffe275f7141429f5f))
* improve error handling in admin handlers ([e948e14](https://github.com/GezzyDax/marzban-telegram-bot/commit/e948e14fba10f47f7a4463c23d228b6def887aa8))

### Code Refactoring

* migrate to callback-based UI with Marzban sync ([113b2ba](https://github.com/GezzyDax/marzban-telegram-bot/commit/113b2ba8a5928a6d98b226491aec598e8362173a))

### Continuous Integration

* add semantic release and GitOps auto-update ([26af5bb](https://github.com/GezzyDax/marzban-telegram-bot/commit/26af5bb1cf343f7d06f2dfffc815f64e9da67c1b))
* restrict Docker build to main branch only and add versioning ([546202b](https://github.com/GezzyDax/marzban-telegram-bot/commit/546202b6103346cf2f4a88299a49de153d95e8a2))
