# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [0.5.0](https://github.com/tks18/pyquery/compare/v0.4.0...v0.5.0) (2025-12-20)


### Build System 🏗

* **packages:** add pydantic for robust type system for the app ([300c395](https://github.com/tks18/pyquery/commit/300c39517feade8ec543e0d76068d29e14134d9c))


### Code Refactoring 🖌

* **backend/helpers:** refactor it to type the module in a robust way ([8345793](https://github.com/tks18/pyquery/commit/83457932792b40398ec349414ab37913dfb0088e))
* **backend/t'forms:** update the column transforms to use the new typing ([21ec6fc](https://github.com/tks18/pyquery/commit/21ec6fcd160a6388ad4acb35f030b2f7f57a59b4))
* **backend/t'forms:** update the row transforms to use the new typing ([8ead3a4](https://github.com/tks18/pyquery/commit/8ead3a4f95645b0dadef6d295a488cebb4157c32))
* **frontend/components:** reflect the recent changes ([86793a6](https://github.com/tks18/pyquery/commit/86793a6033d9554b35e42e38d22a302afa3ef8dc))
* **frontend/components:** update the sidebar to reflect the recent type changes ([39fb966](https://github.com/tks18/pyquery/commit/39fb9667c1a450d81a6a92e2b3c025cddbd1555e))
* **frontend/utils:** refactor the dynamic_ui to support the new typing ([700debd](https://github.com/tks18/pyquery/commit/700debdf23764e74ca5b7360762bafec8af7fed0))


### Features 🔥

* **backend/engine:** rewrite the entire engine from scratch ([bdbe234](https://github.com/tks18/pyquery/commit/bdbe23417c1cc04ffed15d61a5e4c9390a4079f4))
* **backend/io:** rewrite the io helper from scratch so that we load the data faster ([bb56d9e](https://github.com/tks18/pyquery/commit/bb56d9e4b22a15ef68f973227ffc008f92b5801c))
* **backend/io:** use the updated types for loading and support more types using the helpers ([8b44425](https://github.com/tks18/pyquery/commit/8b44425388adc641307e4fc750429153f89ef025))
* **backend/t'forms:** add a new analytics transform functions ([68549d2](https://github.com/tks18/pyquery/commit/68549d2f9573bb4bbd48add619687f8e9655328e))
* **backend/t'forms:** add a new cleaning transform functions ([815f436](https://github.com/tks18/pyquery/commit/815f436d7b0e15161982b9cef88f4db9400c66fd))
* **backend/t'forms:** add new scientific and data transform library ([9ee95fa](https://github.com/tks18/pyquery/commit/9ee95fa8f538db7a33a3d340f054534b1d3dc8b4))
* **backend/t'forms:** rewrite the combine from scratch to be more type proof and error prone ([a0f0a92](https://github.com/tks18/pyquery/commit/a0f0a92175dedce267654fbd1a1ff5ada568cf03))
* **frontend/components:** add a new metadata for the user which shows the file size of the export ([fe4844f](https://github.com/tks18/pyquery/commit/fe4844fd8fcbef3320f4549e1b35523e7584a8a0))
* **frontend/components:** rewrite the recipe_editor completely to reflect the recent changes ([8745b65](https://github.com/tks18/pyquery/commit/8745b652e1321b60589f159344069d06569fa767))
* **frontend/state:** rewrite the state_manager completely to reflect the recent changes ([e963d40](https://github.com/tks18/pyquery/commit/e963d40837d9de4943f3505b0a1a480bd35f6884))
* **frontend/steps:** write all the renderers for the different transform modules ([1ee16b0](https://github.com/tks18/pyquery/commit/1ee16b0f89367769bc4b8be0f04cc8b513518e94))
* **frontend:** create a new renderer function that will dynamically display the step related params ([57c5b7b](https://github.com/tks18/pyquery/commit/57c5b7b21ad8a633484782304a4d9aa72cdecec4))
* **types:** write a registry type for the transformations registrations and management ([7d74143](https://github.com/tks18/pyquery/commit/7d741438246dbeb5d297a5b7bcb4f9d8e39e95a8))
* **types:** write all core models required by the backend engine ([b6435d7](https://github.com/tks18/pyquery/commit/b6435d7c75a4fbb981d895525c3113544ccfd114))
* **types:** write all the io types required for input and export types ([9d5719f](https://github.com/tks18/pyquery/commit/9d5719fb979eada121a1a9ded38bb8e1a4b8c9a5))
* **types:** write all the types required for each transform step ([79d7e1f](https://github.com/tks18/pyquery/commit/79d7e1fe1eaefa677c3730bfd40f03abc4407c54))


### Docs 📃

* **readme:** update the readme to reflect the recent major changes ([9c4a093](https://github.com/tks18/pyquery/commit/9c4a093aacedaedacad713ab44d70a6e0118e677))


### Others 🔧

* chore [space] change ([02bbfcf](https://github.com/tks18/pyquery/commit/02bbfcf217091ad2aa4639d9346bc2b4e568b268))
* chore [space] change ([08d15d4](https://github.com/tks18/pyquery/commit/08d15d4664180aa1b34d24f6c73eb188a6bee261))
* chore changes ([3f40216](https://github.com/tks18/pyquery/commit/3f40216cacff2ccffe2d56e5f536181ceee8c5d3))
* **pyversion:** update the app version to v0.5.0 ([ddbf62f](https://github.com/tks18/pyquery/commit/ddbf62fb38f439c29cfc59640b018306f6a48888))

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
