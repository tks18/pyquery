# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [0.4.0](https://github.com/tks18/pyquery/compare/v0.3.0...v0.4.0) (2025-12-19)

### Code Refactoring 🖌

- **backend:** move all the transformations to backend ([2a95425](https://github.com/tks18/pyquery/commit/2a95425bda6b7dae8fe9532a8f857fc7e20adc55))
- **frontend/components:** remove all legacy code ([980c234](https://github.com/tks18/pyquery/commit/980c2348019c8b62950196e333bbd4acbaffb5ec))
- **frontend:** move the state_manager to the frontend ([494d896](https://github.com/tks18/pyquery/commit/494d8960fb1ca6aae18a40bca052cd80e7d1670a))
- **utils:** removed it as it was moved to backend api ([372e582](https://github.com/tks18/pyquery/commit/372e582e539a587c92693d4ce336389e0f9eef32))

### Features 🔥

- **app:** rewrite the entry point for the app to use the new api ([1cff43f](https://github.com/tks18/pyquery/commit/1cff43ffaf625a237ccadce28ce3d6462da60e24))
- **backend:** move the utils to backend/utils ([f9c1c7e](https://github.com/tks18/pyquery/commit/f9c1c7e2c2ffd5006ac8986489758639c9efc828))
- **backend:** write a new io_plugins module that will handle all input and export loaders ([9135382](https://github.com/tks18/pyquery/commit/9135382f3ef732688e8a597d02e3aef08b74a878))
- **backend:** write the main backend engine / class that will be used by the frontend engine ([0c991e6](https://github.com/tks18/pyquery/commit/0c991e63adcd8406872023bb0ac8381875bdece3))
- **frontend/components:** rewrite the profile tab from scratch to render the ui nicely ([d379e7b](https://github.com/tks18/pyquery/commit/d379e7b7b80c7948b2c93963bc66c001d5c7ce90))
- **frontend/components:** rewrite the sidebar from scratch to use the new engine api ([f666435](https://github.com/tks18/pyquery/commit/f666435c276a227511f8a022baf91714ff9b4083))
- **frontend/components:** write a new export component that shows more metadata ([1e8fe20](https://github.com/tks18/pyquery/commit/1e8fe2089d08f2cc75a639b3dfe1d849e19423f1))
- **frontend/components:** write a new recipe render component that displays dynamically ([0d6e13d](https://github.com/tks18/pyquery/commit/0d6e13d1df5babf0291e263932008278a7244b69))
- **frontend:** write a new dynamic_ui renderer function to dynamically display the transformations ([ac7fcb5](https://github.com/tks18/pyquery/commit/ac7fcb5d8576d1c8da482483a2092a2315ed6b51))
- **frontend:** write all the renderers for the transformation steps required by the backend ([67e8c46](https://github.com/tks18/pyquery/commit/67e8c469d6e430b737e51820166d73ccc55e594b))

### Docs 📃

- **readme:** update readme ([a0afd85](https://github.com/tks18/pyquery/commit/a0afd85992c0dc1e7cd03372c0e4e73cd1eb1993))
- **readme:** update the readme to reflect the recent changes ([da23804](https://github.com/tks18/pyquery/commit/da238047167d576ce19ca56cbb91f73335540ba2))

### Others 🔧

- update the app version to v0.4.0 ([8f873c1](https://github.com/tks18/pyquery/commit/8f873c11043926338ebb7e0124a51ebc4a409ee6))

## [0.3.0](https://github.com/tks18/pyquery/compare/v0.2.0...v0.3.0) (2025-12-18)

### Features 🔥

- **app/utils:** write a parsing utility for different datat types ([cbb2a25](https://github.com/tks18/pyquery/commit/cbb2a2592feed541fb9710219cfc36676c63a612))
- **app/utils:** write all helpers function (modularize) ([7a3c665](https://github.com/tks18/pyquery/commit/7a3c6650cde1a683e51ec1b75a3db7afe843a163))
- **app/utils:** write io utils (modularize) ([d21b233](https://github.com/tks18/pyquery/commit/d21b233e2a7aa5ccd8f98afd3e14020b657ee400))
- **app:** write the main app entry point by modularizing the entire app components ([3fe170c](https://github.com/tks18/pyquery/commit/3fe170c72a66c57ef28ffddd254c244ec597788b))
- **app:** write the main app state manager api ([35eb784](https://github.com/tks18/pyquery/commit/35eb784cc396ecc4eccccbe498a03b33b2f34067))
- **ui:** add the export component ([bacda79](https://github.com/tks18/pyquery/commit/bacda798df82cb8af4f7a54d060ad9ffa53d43a9))
- **ui:** write the profile tab (modularize) ([9739abf](https://github.com/tks18/pyquery/commit/9739abfe1e1da31fa7f1803d16d9ccb7da9836f5))
- **ui:** write the sidebar for the app (modularize) ([79da3e8](https://github.com/tks18/pyquery/commit/79da3e83f751e10d13900f5d137c91ad8fbd733c))
- **ui:** write the steps editor component (modularize) ([934a780](https://github.com/tks18/pyquery/commit/934a780a1074ca04ef44621bb5beca4e8be8d0de))

### Others 🔧

- package.json ([0a2a42d](https://github.com/tks18/pyquery/commit/0a2a42d346622f72a6082a0959f68586d355cc34))
- **pyversion:** update the app version to v0.3.0 ([15a98f1](https://github.com/tks18/pyquery/commit/15a98f1366cfddfd88a8e566673aef3235e8b0ef))
- update pyversion ([27a7cfc](https://github.com/tks18/pyquery/commit/27a7cfcd6594bca28b109f2dedd6e88c7fa904f4))

## 0.2.0 (2025-12-18)

### Features 🔥

- **ci:** add husky, commitlint, standard-version for standard commit linting ([8a15a5a](https://github.com/tks18/pyquery/commit/8a15a5ad642d4bd6ab374ad7babf9303827fd833))
