# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [4.1.0](https://github.com/tks18/pyquery/compare/v4.0.0...v4.1.0) (2026-01-27)


### Code Refactoring 🖌

* **cli/branding:** refactor branding to multiple sub modules for development exp ([7de839d](https://github.com/tks18/pyquery/commit/7de839da3fbdb6cf7276be6457d9bbaf2158585e))
* **cli/headless:** refactor headless completely into submodules for better developer exp ([0801ae2](https://github.com/tks18/pyquery/commit/0801ae215009d45531ddf527cd5e75d37caf5eb7))
* **cli/main:** refactor the main to use the new parsers, thememanager & headless pipelines ([1f1cfa7](https://github.com/tks18/pyquery/commit/1f1cfa7476824ed6c43035719e66dc4c710cd99f))


### Others 🔧

* **pyversion:** update app to 4.1.0 ([1697b23](https://github.com/tks18/pyquery/commit/1697b237249345483e70807b0ce1cde0aed3728b))

## [4.0.0](https://github.com/tks18/pyquery/compare/v3.0.0...v4.0.0) (2026-01-26)


### Bug Fixes 🛠

* **backend/recipes:** update infer types step to resolve to a proper label if custom lbl is used ([18a4ce6](https://github.com/tks18/pyquery/commit/18a4ce63793878d9c85c94590f046e5204e621a3))
* **core/registry:** update frontend func model for proper function signature ([cda3616](https://github.com/tks18/pyquery/commit/cda36163c5c01b769e13ed81d4c08878fb67753a))
* **frontend/utils:** styles: overflow issue in eda tab fixed ([04303c0](https://github.com/tks18/pyquery/commit/04303c09f4c94f52945445c9e764a90d33b90d62))


### Features 🔥

* **backend/recipes:** add a function to remove a recipe step ([ea28b91](https://github.com/tks18/pyquery/commit/ea28b91d6d1d317f7391963e52f9dc023f93677e))
* **frontend/base:** create a base component class which will provide the context and state ([65af491](https://github.com/tks18/pyquery/commit/65af4910b16a115ed8aefb1d306885105211caa6))
* **frontend/base:** create a context class that will give access to all shared resources ([dd3f293](https://github.com/tks18/pyquery/commit/dd3f293440271ed95f6216ec0e6776eacfc1caf3))
* **frontend/base:** state: shared state manager for all components for safe state access ([e96d0ef](https://github.com/tks18/pyquery/commit/e96d0ef259207347183570f9d575ac5763a8e340))
* **frontend/components:** api-loader: create a class based component ([b5cddec](https://github.com/tks18/pyquery/commit/b5cddec99bbcbe09a967180680ea23ebff301adc))
* **frontend/components:** create a base dialog loader class ([c22387c](https://github.com/tks18/pyquery/commit/c22387c774965e670fbf6a78f271371b28e98087))
* **frontend/components:** eda: complete class based reimplementation of eda tab ([5f8c0af](https://github.com/tks18/pyquery/commit/5f8c0afe13afd8786422264d05476212579b77c3))
* **frontend/components:** export: create a class based component ([572fb09](https://github.com/tks18/pyquery/commit/572fb092900a80b0d62ae41c50421cc0c3043bd8))
* **frontend/components:** file-loader: create a class based component ([e2b5fc1](https://github.com/tks18/pyquery/commit/e2b5fc1b7ca8900b38c0cd35d0a8a13952fbc1a5))
* **frontend/components:** loader-utils: fix autoinference and introduce new apis ([77f7268](https://github.com/tks18/pyquery/commit/77f7268e17d341cea7d8efa6ebe6b4074684fbe0))
* **frontend/components:** profile: create a class based component ([7c97868](https://github.com/tks18/pyquery/commit/7c978686d28b44d1c3c56a2d2238b3d28f9e6421))
* **frontend/components:** project_dialog: create a class based component ([2b2fa89](https://github.com/tks18/pyquery/commit/2b2fa89a1d70360bfbde6a683685fb0fd934a2da))
* **frontend/components:** recipe_editor: create a class based component ([e4dacbe](https://github.com/tks18/pyquery/commit/e4dacbe76867ac4fdb2c192453f2d783d21df4b8))
* **frontend/components:** sidebar: create a class based component ([7b4229f](https://github.com/tks18/pyquery/commit/7b4229f32392c7d039cf78fb8dd1fe6ed854c93f))
* **frontend/components:** sql_tab: create a class based component ([044d23f](https://github.com/tks18/pyquery/commit/044d23f610fc193b55e51806a1d6a20a416114c4))
* **frontend/components:** sql-loader: create a class based component ([59a4355](https://github.com/tks18/pyquery/commit/59a4355ca7cbb7bf36967959aeb92b617deb5b4e))
* **frontend/transforms:** create the base step renderer that will be used by all transform pipeline ([ddbadc8](https://github.com/tks18/pyquery/commit/ddbadc890f87940856478da518f74625090bb4e8))
* **frontend/transforms:** move every step to transforms folder (apt name) + class based components ([f21bf86](https://github.com/tks18/pyquery/commit/f21bf861490d8d01542b1dca4486a144d0e10a12))
* **frontend/transforms:** move the registry to transforms + introduce class based access ([73ea061](https://github.com/tks18/pyquery/commit/73ea061f5e6d652cfc42a151cabaeced3300645e))


### Styling 🎨

* **backend/jobs:** linter changes ([d85ba8f](https://github.com/tks18/pyquery/commit/d85ba8f7cb1fba791a969955da030303e4cb9812))
* **frontend/base:** export base abstract & data classes ([7001d11](https://github.com/tks18/pyquery/commit/7001d1125614ec48492deea6a91c1684d94f4106))
* **frontend/components:** export classes ([4b97595](https://github.com/tks18/pyquery/commit/4b97595fcd68eb09a1814403a47bb05a114e8b3f))
* **frontend/components:** loader: exports ([8e0c823](https://github.com/tks18/pyquery/commit/8e0c82334ee7e86408e8df2fe1e7f14ac247476a))
* **frontend/elements:** export all the elements ([63fe048](https://github.com/tks18/pyquery/commit/63fe04805a34b1a1f6b7d3d18995d4d1e865af6a))
* **frontend/transforms:** export the functions ([beb5d64](https://github.com/tks18/pyquery/commit/beb5d6418fadd12c1e8602717d16dac645a5b616))
* **frontend/utils:** completions: linter changes ([d043348](https://github.com/tks18/pyquery/commit/d0433482f84e3d5484c4da7d8389d244f7082082))


### Code Refactoring 🖌

* **frontend/elements:** move code_editor from custom_components to elements (its apt name) ([6e5403a](https://github.com/tks18/pyquery/commit/6e5403a0c61de97c1e04fe40617e486f1b674165))
* **frontend/elements:** move editor elements to elements folder ([3bd8dff](https://github.com/tks18/pyquery/commit/3bd8dffb7ec5148d323ec6079aecc6bc4500043d))
* **frontend/statemanager:** remove legacy state manager code as its replaced by context mgr ([d361768](https://github.com/tks18/pyquery/commit/d361768ad7cc9f4b42ffd5b6586025eea8efdc4a))
* **frontend/utils:** renderers: update the api for stepregistry ([c70149a](https://github.com/tks18/pyquery/commit/c70149a08800d83f43a63dceddb95ce512092d9f))
* **frontend:** completely refactor the entry point ([7c50ddc](https://github.com/tks18/pyquery/commit/7c50ddcf9ddeea4252543a99f056ea3e36cf2cb9))


### Others 🔧

* **pyversion:** update app version to 4.0.0 ([5e32bf7](https://github.com/tks18/pyquery/commit/5e32bf768e5f95235e2b118a966e32d8580121b8))

## [3.0.0](https://github.com/tks18/pyquery/compare/v2.8.0...v3.0.0) (2026-01-25)


### Styling 🎨

* **api/routes:** files: linter refactor ([e2c027a](https://github.com/tks18/pyquery/commit/e2c027a44c8ac8cc6bf1fdfc80a08ad9e120d28b))
* **api:** auth: linter refactor ([de7a65c](https://github.com/tks18/pyquery/commit/de7a65cb770b19e87c584070a59021f6ad7d750d))
* **api:** db: linter refactor ([3e01bd9](https://github.com/tks18/pyquery/commit/3e01bd98aa84268770718ba97806e26e00d18def))
* **backend/analytics:** import refactor for consistency ([7f9fda7](https://github.com/tks18/pyquery/commit/7f9fda79fea7a7029c3edde7a688fc5527fcf729))
* **backend/datasets:** export dataset manager ([d6bfdfd](https://github.com/tks18/pyquery/commit/d6bfdfd9b8d3f20c998ad6e523d41905addb4f22))
* **backend/datasets:** import refactor for consistency ([aac5fff](https://github.com/tks18/pyquery/commit/aac5fff6cf1b4360507de4babbfa4ecf9a79f691))
* **backend/io:** import refactor for consistency ([98d32ca](https://github.com/tks18/pyquery/commit/98d32ca7b63122483f62840d286d1a55e4d06daf))
* **backend/io:** plugins: linting refactor ([ae7c253](https://github.com/tks18/pyquery/commit/ae7c253861c6e6ebb6406d4b4be3972f72b0365c))
* **backend/jobs:** export job manager ([10b4ce3](https://github.com/tks18/pyquery/commit/10b4ce351ef0457464e894a40d35c94e81d19db3))
* **backend/jobs:** import refactor for consistency ([48b8395](https://github.com/tks18/pyquery/commit/48b83959978ade86a08e75543e516c74bb067b98))
* **backend/processing:** executor: linting changes ([31efafd](https://github.com/tks18/pyquery/commit/31efafd59cebc1fb8a7d080e33787fb4bc2b50c4))
* **backend/processing:** export processing manager ([4a76309](https://github.com/tks18/pyquery/commit/4a76309b369d60ce5fb9585263ebdc1282cafb8a))
* **backend/processing:** import refactor for consistency ([355e4b5](https://github.com/tks18/pyquery/commit/355e4b5a4892ff4f8dc9dd24c434ff1371706cbd))
* **backend/projects:** import refactor for consistency ([3d9853e](https://github.com/tks18/pyquery/commit/3d9853ed89b6920d16de3947ac111faa656bcfa6))
* **backend/recipes:** export recipe manager ([89faebc](https://github.com/tks18/pyquery/commit/89faebcc0586a669dd7d67b602eba1cd3b530889))
* **backend/recipes:** import refactor for consistency ([fecddfc](https://github.com/tks18/pyquery/commit/fecddfc98a942a5b3583efd11823c26aeffbf442))
* **backend/transforms:** export transform registry ([8776b8f](https://github.com/tks18/pyquery/commit/8776b8f65f2f35bcc4089292e1890d13d8bfcbb7))
* **backend/transforms:** import refactor for consistency ([3cb2d9b](https://github.com/tks18/pyquery/commit/3cb2d9be656d0511f20d9e338f56a3e4016e8edd))
* **backend/utils:** parsing: linter changes ([382aec3](https://github.com/tks18/pyquery/commit/382aec3dd4827aecbf619f87873ecd05637254a4))
* **cli/branding:** linter changes ([3d4a639](https://github.com/tks18/pyquery/commit/3d4a639e41d7c320db4b31b7676ef1d4bba32e3d))
* **core/io:** linter changes ([ab2b0b7](https://github.com/tks18/pyquery/commit/ab2b0b7e8dd503bc7df99a883e0f1daa91243777))
* **core/models:** linter changes ([d2f8cb1](https://github.com/tks18/pyquery/commit/d2f8cb13388e69548c7cb3936caf7373a9268ec0))
* **core/params:** linter changes ([cd9baaa](https://github.com/tks18/pyquery/commit/cd9baaa8cba5f21cb92bb0d1328caecd8c4477c6))
* **core/project:** linter changes ([7e6a6b9](https://github.com/tks18/pyquery/commit/7e6a6b9f9cd967e9493227090385aaa2d569896b))
* **core/registry:** linter changes ([2f6844e](https://github.com/tks18/pyquery/commit/2f6844e03c344d5ac9315878e3f190013e4e144d))
* **frontend/components:** eda: core - linter changes ([2882581](https://github.com/tks18/pyquery/commit/288258110b268c932a595b940091d03ca48a479d))
* **frontend/components:** editor: linter changes ([203d05e](https://github.com/tks18/pyquery/commit/203d05ea2a0f184621ad98030e51c97629aae193))


### Features 🔥

* **backend/analytics:** create a new analytics manager that will takeover all analytical ops ([163e10c](https://github.com/tks18/pyquery/commit/163e10cee3b8af24f43a07ee569ff26265edf3d8))
* **backend/core:** now new core engine will act as a true orchestrator for all sub modules ([f8fab36](https://github.com/tks18/pyquery/commit/f8fab36f7053bb87cf21603d6c580bb6bd772a5c))
* **backend/datasets:** dataset manager for doing all CRUD operations related to datasets ([b1cdbb7](https://github.com/tks18/pyquery/commit/b1cdbb719e7db8d9ddd98c95625827399991b4bc))
* **backend/io:** create iomanager that will focus on all IO operations now ([88de35f](https://github.com/tks18/pyquery/commit/88de35ff81c1bf29fce584f6dcab5a88550a8a57))
* **backend/jobs:** create job manager that will perform all Job related ops ([ab33317](https://github.com/tks18/pyquery/commit/ab333175a3efa81a1150757eb765a4d1efda2b69))
* **backend/processing:** create processing manager that will handle all execution related ops ([b809f12](https://github.com/tks18/pyquery/commit/b809f126dac4417a8ab8caf496a5df033f594e13))
* **backend/projects:** create a project manager for handling project import / export ([611c20a](https://github.com/tks18/pyquery/commit/611c20ad4a8f64e06f11f9acecadd14810fe0d38))
* **backend/recipes:** create recipe manager for all CRUD related to recipes ([6dbfc19](https://github.com/tks18/pyquery/commit/6dbfc1964fbd720d346e22f57676b909f3a6d8b5))
* **backend/transforms:** create transform registry for all registration and operations of t'ions ([028de67](https://github.com/tks18/pyquery/commit/028de67cead47be8de28522fab38a5c685b3828d))
* **main:** add runcliapp method to the main exports ([1691e04](https://github.com/tks18/pyquery/commit/1691e04794ed761a03b40a9b0dd70345a222c242))


### Code Refactoring 🖌

* **api/routes:** datasets: engine refactor to new api ([4b38188](https://github.com/tks18/pyquery/commit/4b3818828fac29bbd2fad3d13a40a88717dfd3af))
* **api/routes:** meta: engine refactor to new api ([d2f501f](https://github.com/tks18/pyquery/commit/d2f501f3ab82f3c04663d6c4636582bce0c5f515))
* **api/routes:** recipes: engine refactor to new api ([69b3b2d](https://github.com/tks18/pyquery/commit/69b3b2d85aa8841dd2ab4a612409fbde17acdb3f))
* **api:** dependencies: engine refactor to new api ([fc1e2b6](https://github.com/tks18/pyquery/commit/fc1e2b6207175fc8f4b05d653561a022dff4c60c))
* **api:** engine refactor to new api ([71c91b1](https://github.com/tks18/pyquery/commit/71c91b17f05e8485e9ccfd7ee2943360c84f3f65))
* **app:** refactor to the new entry point ([07cb4b6](https://github.com/tks18/pyquery/commit/07cb4b63e790ecfe89a29ae2075780265fe07058))
* **backend/analysis:** remove old analysis folder ([2813515](https://github.com/tks18/pyquery/commit/28135150a59e1b2ff9ac61e1be7f82bb5cc60c8a))
* **backend/analytics:** inference: move analysis to analytics folder ([d93504c](https://github.com/tks18/pyquery/commit/d93504c9b1d3b2a2ec312b17a005813a3155b3ba))
* **backend/analytics:** joins: move analysis to analytics folder ([05f4c15](https://github.com/tks18/pyquery/commit/05f4c158626a4d438a6f79a24dc3a7ab803584d9))
* **backend/analytics:** ml: move analysis to analytics folder ([0540a77](https://github.com/tks18/pyquery/commit/0540a770c40d202929b3c2593aece999e6dbba91))
* **backend/analytics:** stats: move analysis to analytics folder ([b3b25b9](https://github.com/tks18/pyquery/commit/b3b25b91e428f5ec1761121757a7ee690b919783))
* **backend/core:** now export the correct core backend engine ([d1f1ed5](https://github.com/tks18/pyquery/commit/d1f1ed5f9cfc10a22dd8708b657eddae9e95f9cc))
* **backend/core:** remove all unwanted / legacy code ([c81e8c0](https://github.com/tks18/pyquery/commit/c81e8c0479dfe0d67d3bcfa7e69a2a9808b70a0d))
* **backend/io:** files - style refactors & preparation for manager ([0b9702c](https://github.com/tks18/pyquery/commit/0b9702cee6ed70c94005b71899b5e570df7b46df))
* **backend/processing:** materializer: rename for appropriate function ([48c85d8](https://github.com/tks18/pyquery/commit/48c85d87467d9bad7e257e571a72f637cfc5bd39))
* **backend/projects:** now export the project manager ([422c61d](https://github.com/tks18/pyquery/commit/422c61d05b940053a106ea8a158977acd6b611b6))
* **backend/projects:** serializer: move from project to projects ([4f75202](https://github.com/tks18/pyquery/commit/4f752028ed2075129d91d941761cc019e0c4e30e))
* **backend/transforms:** move the transform functions to its own transform folder -> pipeline ([a8fa4fb](https://github.com/tks18/pyquery/commit/a8fa4fb0f28b1c7f7295f5aa76a1ddbb1ed89f9e))
* **cli/headless:** engine refactor to new api ([1fb9aaa](https://github.com/tks18/pyquery/commit/1fb9aaace361d50ded48c385ae185c4ad1844c5d))
* **cli/main:** move cli/main to main folder as this is the entrypoint ([87b3ed9](https://github.com/tks18/pyquery/commit/87b3ed9617a272b272d087a2e0153769dbe5e06f))
* **frontend/app:** refactor app main entrypoint ([0e5577e](https://github.com/tks18/pyquery/commit/0e5577eb56baadbb3f2c48707c039e2b5de4648b))
* **frontend/components:** api-loader: engine refactor to new api ([28978a2](https://github.com/tks18/pyquery/commit/28978a20147227b69bdb48321fe9ae1138abb886))
* **frontend/components:** eda: contrast - engine refactor to new api ([9659266](https://github.com/tks18/pyquery/commit/9659266b4ae37d6bcf4393e3d83cfdf02b99d68d))
* **frontend/components:** eda: engine refactor to new api ([2388465](https://github.com/tks18/pyquery/commit/2388465b8c3a8760459ee4906c46d2ecc2e67785))
* **frontend/components:** eda: ml - engine refactor to new api ([04aa248](https://github.com/tks18/pyquery/commit/04aa24866f87243b8c9e4684bb75cd606f01c024))
* **frontend/components:** eda: overview - engine refactor to new api ([ef7318a](https://github.com/tks18/pyquery/commit/ef7318a6c4a0c31a1c853e6295613518465e05fc))
* **frontend/components:** eda: overview - engine refactor to new api ([7b6cfd6](https://github.com/tks18/pyquery/commit/7b6cfd6b2f0338d2565576870e8b04f5b4e7e472))
* **frontend/components:** eda: plots - engine refactor to new api ([0a5650f](https://github.com/tks18/pyquery/commit/0a5650f5fc84067a3a1c55231fb9c7e2daa311c7))
* **frontend/components:** eda: profiling - engine refactor to new api ([eca5922](https://github.com/tks18/pyquery/commit/eca59229cf281e882ca244dcea907f8e18d3b565))
* **frontend/components:** eda: simulation - engine refactor to new api ([46ea5ca](https://github.com/tks18/pyquery/commit/46ea5ca95d8980da4c4b8d474e7f046c13474f15))
* **frontend/components:** export - engine refactor to new api ([bf74784](https://github.com/tks18/pyquery/commit/bf747847c09d2213109a9897c6658593e9aa152b))
* **frontend/components:** file-loader: complete refactor to new api ([6102d78](https://github.com/tks18/pyquery/commit/6102d7845b58940736b9fc89b4f1b4779f7ef140))
* **frontend/components:** profile - new api refactor ([a57587f](https://github.com/tks18/pyquery/commit/a57587fba750ef3c097be250cab3a248e3e7994e))
* **frontend/components:** project-dialog: complete refactor to new api ([846d4f5](https://github.com/tks18/pyquery/commit/846d4f55e48824d8c37d7e3d2fe3ab876ea7848c))
* **frontend/components:** recipe-editor: complete refactor ([49219ad](https://github.com/tks18/pyquery/commit/49219ade914e603a284a1b9b61424b2ba661493b))
* **frontend/components:** sidebar: refactor for new backend api ([f95987c](https://github.com/tks18/pyquery/commit/f95987cd550eb4ed7dcda48ba6857972b39dbc55))
* **frontend/components:** sql-loader: engine refactor to new api ([9287dca](https://github.com/tks18/pyquery/commit/9287dca22161b7afa756e34fd105385f8d200326))
* **frontend/components:** sql-tab: new api refactor ([77c3d48](https://github.com/tks18/pyquery/commit/77c3d4868bad1e6c119761976f88ee97f97c1079))
* **frontend/state:** new apis to sync from the backend recipes ([c54b7a8](https://github.com/tks18/pyquery/commit/c54b7a837af27a1f829a4ac01ef5a7f23572a760))
* **frontend/steps:** linter + new api refactor ([85f4216](https://github.com/tks18/pyquery/commit/85f4216e742db4c4427a7571bc342e58f7acea91))
* **frontend/utils:** cache: new engine refactor ([5c370d5](https://github.com/tks18/pyquery/commit/5c370d57eefc1806904e7bc356a7210cfed6facf))
* **frontend/utils:** linter refactor ([95bd03b](https://github.com/tks18/pyquery/commit/95bd03b11c7be5aff1b63de76d93aa0529d4dfd1))
* **frontend/utils:** use the new auto inference api ([c815d77](https://github.com/tks18/pyquery/commit/c815d770432d15136d20d81c48ac0a0db4bda187))
* **pyproject/script:** update entry point in script to refer new main.py ([6557c1c](https://github.com/tks18/pyquery/commit/6557c1c56213e287169f92cc7114c57b2b5c6ac2))


### Build System 🏗

* **pyproject:** update app to 3.0.0 Major version ([98fdf15](https://github.com/tks18/pyquery/commit/98fdf150fcc97e6d15c62fca08a9d42ac8894074))

## [2.8.0](https://github.com/tks18/pyquery/compare/v2.7.0...v2.8.0) (2026-01-24)


### Features 🔥

* **backend/core:** move the auto type infer step to the backend ([b17235a](https://github.com/tks18/pyquery/commit/b17235aa69deb98510edf934e5f78473f3f34998))
* **cli/headless:** now use sql to transform the loaded data on the fly and save it, all headless ([25e4031](https://github.com/tks18/pyquery/commit/25e4031c73221fd395bfcb23705f038a66cf61bc))
* **cli/main:** add split-files, transform-sql & alias for additional functionality ([3ba77d4](https://github.com/tks18/pyquery/commit/3ba77d43979b926bc15ed09d9ed15ff7a9b4c966))
* **frontend/components:** file-loader: new feature: split files now available ([1cea0dd](https://github.com/tks18/pyquery/commit/1cea0dd5eda2ea2ccc347ead77921c9ff1964ad9))
* **frontend/utils:** use the new backend api for infer types ([86bff41](https://github.com/tks18/pyquery/commit/86bff416f86245bb0fc9c875a061fe64d24ac523))


### Others 🔧

* **pyversion:** update app to 2.8.0 ([62167fd](https://github.com/tks18/pyquery/commit/62167fd36b536707b80b9d9efea70e5f827a4ef0))

## [2.7.0](https://github.com/tks18/pyquery/compare/v2.6.2...v2.7.0) (2026-01-24)


### Code Refactoring 🖌

* **core/io:** rename the file io_params -> io.py ([b8f1b54](https://github.com/tks18/pyquery/commit/b8f1b54e08d6852182e74815eb88a35fe4d77b55))


### Features 🔥

* **backend/core:** multiple features -> recipe storage + project handling ([542e39d](https://github.com/tks18/pyquery/commit/542e39d2d6e7b867933450d6e2130da9545d3b1c))
* **backend/io:** add a new export function for use by cli to export directly ([720457c](https://github.com/tks18/pyquery/commit/720457c243bd475d7a9e5d9c1420002887557d49))
* **backend/io:** allow for setting staging path using env ([79456e7](https://github.com/tks18/pyquery/commit/79456e70d0768233814f99b044e4ca6e88c50a64))
* **backend/project:** add handlers for loading/saving project files ([4ee6bdf](https://github.com/tks18/pyquery/commit/4ee6bdfb7e54fe89efcc5ea130336fc95ad384e3))
* **cli/branding:** update branding.py to add more helper functions for cli headless ([e4ab965](https://github.com/tks18/pyquery/commit/e4ab9652db88ea837fcad95fb29a649d9da3d88b))
* **cli/headless:** completely revamp headless to support all the features from backend ([7c99d58](https://github.com/tks18/pyquery/commit/7c99d58721c252c8db1543c5ff19f798f8915602))
* **cli/interactive:** remove interactive as its a low usage tool ([da5d537](https://github.com/tks18/pyquery/commit/da5d537cf4af633cb4958641352c8021a71307e7))
* **cli/main:** implement new features from backend, remove interactive ([7a98c31](https://github.com/tks18/pyquery/commit/7a98c311b4bfc62ece62ea0dd77a218da8b8dfbd))
* **core:** introduce project capabilities - params for handling project files ([569ffda](https://github.com/tks18/pyquery/commit/569ffda174ff792d14174b3556dd885f6dd47555))
* **frontend/components:** introduce project dialog handlers, now save and load project files ([c9d31a4](https://github.com/tks18/pyquery/commit/c9d31a40a1ab1c7402d92325576ca915e96d0237))
* **frontend/components:** sidebar: add project import / export buttons ([539de1a](https://github.com/tks18/pyquery/commit/539de1ad58181ecc21dca09e925aaa711c45615e))
* **frontend/state:** update state manager to sync recipes from backend ([964af00](https://github.com/tks18/pyquery/commit/964af0019e7357276a6f489d05f313ade349a54d))
* **frontend/utils:** sync the auto infer step to the backend ([ff84b15](https://github.com/tks18/pyquery/commit/ff84b15c1a527c1081dee46100a2bcb741e11e36))


### Bug Fixes 🛠

* **cli/main:** by mistake deleted ui related parsers, added back ([0c1eb3a](https://github.com/tks18/pyquery/commit/0c1eb3af199ccd3cc7a846f5b569d1755108f10e))
* **frontend/components:** file-loader: sheet / table didnt get populated when editing ([806ea08](https://github.com/tks18/pyquery/commit/806ea08a8642953b35a98ab71be44ed94827f9cb))


### Docs 📃

* **readme:** update readme to reflect recent changes ([b4ef9d5](https://github.com/tks18/pyquery/commit/b4ef9d57e55f112fb8c19ad794627acb63f8f8c7))


### Others 🔧

* **pyversion:** update app to 2.7.0 ([370b798](https://github.com/tks18/pyquery/commit/370b7985d0085915ae1b887d3309cc29e7380c41))

### [2.6.2](https://github.com/tks18/pyquery/compare/v2.6.1...v2.6.2) (2026-01-24)


### Features 🔥

* **backend/io:** update staging dir to use a sub folder with dataset name for proper organization ([bb9717d](https://github.com/tks18/pyquery/commit/bb9717d83d2e7589f5ca0bda8fbc408f4e0a86ba))


### Code Refactoring 🖌

* **backend/io:** pass dataset name to load_lazy function ([55d109b](https://github.com/tks18/pyquery/commit/55d109b02f9c737ca9993521f3eb9483767988ee))
* **backend/io:** refactor to use the new staging folder ([3675f24](https://github.com/tks18/pyquery/commit/3675f24af32436de09771a9743406291605fb9f5))
* **backend/processing:** refactor to use the new staging function ([049f4f8](https://github.com/tks18/pyquery/commit/049f4f80ca6b86f2223c667a8bb103e2755cc53a))


### Others 🔧

* **pyversion:** update app to 2.6.2 ([d7d8994](https://github.com/tks18/pyquery/commit/d7d8994bd77b601d8752de7742cc949eadba28d2))

### [2.6.1](https://github.com/tks18/pyquery/compare/v2.6.0...v2.6.1) (2026-01-18)


### Styling 🎨

* **frontend/components:** file-loader: add emoji ([7d88fe6](https://github.com/tks18/pyquery/commit/7d88fe60bb82bb7fba68a6bb8f0cccc637a03960))


### Bug Fixes 🛠

* **frontend/components:** file-loader: restoring of excel settings on edit not proper ([ac03f5f](https://github.com/tks18/pyquery/commit/ac03f5fbcd22a9e3277989d81515f5d80d44c93f))
* **frontend/components:** file-loader: use the space better for excel settings ([1785deb](https://github.com/tks18/pyquery/commit/1785debc0eb8235e159f356315d572fca544a281))


### Others 🔧

* **pyversion:** update app to 2.6.1 ([042931e](https://github.com/tks18/pyquery/commit/042931e63234f0657877c7d7a04faef2d4fba6c5))

## [2.6.0](https://github.com/tks18/pyquery/compare/v2.5.0...v2.6.0) (2026-01-18)


### Docs 📃

* **readme:** update readme ([8276f96](https://github.com/tks18/pyquery/commit/8276f96e9126505cdca7f7cc0cf168ab7b602de4))


### Bug Fixes 🛠

* **backend/transforms:** advanced: fix the variables being passed to env ([1c0b924](https://github.com/tks18/pyquery/commit/1c0b924503156be68685577124d2f80f88bacdab))
* **frontend/components:** eda: sometimes the fingerprint gets wrongly created ([f8d0206](https://github.com/tks18/pyquery/commit/f8d02061bded2466cb2faaeaff17e19c4de48d25))


### Build System 🏗

* **pyproject:** add sqlalchemy as dependency for sql workflows ([97ebe4c](https://github.com/tks18/pyquery/commit/97ebe4c947cc867f27675bd66c53a367b47490a1))


### Features 🔥

* **backend/core:** expose the api for getting table names ([a759fad](https://github.com/tks18/pyquery/commit/a759fad2ff8b64ed203bbc1689f48b7197fcc9c7))
* **backend/core:** support additional meta related to loader to be stored in backend ([068b730](https://github.com/tks18/pyquery/commit/068b730f4c5602ece0b976af71e603d30c1535d4))
* **backend/io:** app now supports dynamic filters being applied for excel sheets/tables ([6c04e6f](https://github.com/tks18/pyquery/commit/6c04e6f13f6543e1a36cf4e299882fb8e08cd6d9))
* **backend/io:** now supports excel tables as well as inputs ([1ff81d0](https://github.com/tks18/pyquery/commit/1ff81d0acc02428e8cf683e5944e3bc2d42b1609))
* **backend/io:** plugin: update function signature for file loader ([fc26d21](https://github.com/tks18/pyquery/commit/fc26d210b419f6970563f5800638a565bde90b6c))
* **cli/core:** update cli to support dev flag for testing the app ([fc6c40e](https://github.com/tks18/pyquery/commit/fc6c40e4786d7cf91f97cb7df9b3f6e6f02d646d))
* **cli:** when dev mode is enabled, watch for entire root not only frontend ([25c3faf](https://github.com/tks18/pyquery/commit/25c3fafc76e7dc36bb22b093d3b31a55a70010e0))
* **frontend/components:** file-loader: completely revamp - enable sup for dynamic filters, tables ([d363bfb](https://github.com/tks18/pyquery/commit/d363bfbdb892eaad0f46cb3ec4d3710e3b7d0aa9))
* **frontend/components:** now file loader supports edit mode ([d941b3a](https://github.com/tks18/pyquery/commit/d941b3a917f3f06d417468c62ddc746d7a171358))
* **frontend/components:** recipe-editor: allow to view raw source before t'ions, beautify overview ([e948e51](https://github.com/tks18/pyquery/commit/e948e51835c5da29ed963d9543421f0f50982384))
* **frontend/components:** sidebar: support editing of dataset settings after loading ([1cc0cae](https://github.com/tks18/pyquery/commit/1cc0cae25a04e845b8d6b7b0ec809928582dd0c9))
* **frontend/components:** support edit mode for api-loader as well ([859621d](https://github.com/tks18/pyquery/commit/859621db3bf71485d92d74e713cb059230315624))
* **frontend/components:** update sql_loader to support edit mode ([801224e](https://github.com/tks18/pyquery/commit/801224e8264c366f15bfa1791d3322c84dac4494))
* **frontend/utils:** now auto inference also supports edit mode and works at later point of time ([abe96d6](https://github.com/tks18/pyquery/commit/abe96d6b97f8e8ae4c4216bb58e0d362565cb557))
* **frontend/utils:** write cache helpers for table names and dynamic filter support ([97c2208](https://github.com/tks18/pyquery/commit/97c22089066342b89ccd1225ed8837ffc704da71))
* **frontend/utils:** write utils for caching table names for rerender ([78ec974](https://github.com/tks18/pyquery/commit/78ec9746e4953424ff1f1e46c75891a054b14417))
* **models:** update datasetschema to support additional metadata for loader ([2c1bf3b](https://github.com/tks18/pyquery/commit/2c1bf3b71fb8a166c54fd04b94e730eeb17941ec))
* **params:** update io params to support item filters and table names ([318506c](https://github.com/tks18/pyquery/commit/318506cdde124f7865b0b295e5aeaad1d4c4d763))


### Styling 🎨

* **backend/jobs:** linter changes ([39f9485](https://github.com/tks18/pyquery/commit/39f948512e52791421f1556034cf6aeb05374ba6))
* **frontend/components:** fix pylance error ([0072c04](https://github.com/tks18/pyquery/commit/0072c0440ead6055a9b2e54921a6cb98efb7c6ef))


### Others 🔧

* **pyversion:** update app to v2.6.0 ([61a5c87](https://github.com/tks18/pyquery/commit/61a5c87d552ebd7a9b102051758de2d1bfc5940c))

## [2.5.0](https://github.com/tks18/pyquery/compare/v2.4.0...v2.5.0) (2026-01-15)


### Bug Fixes 🛠

* **frontend/app:** fix mimetypes for js, css since sometimes cause isssues with custom components ([595519a](https://github.com/tks18/pyquery/commit/595519a1053b71bb2d78e2dee472d186762419ed))


### Features 🔥

* **backend/core:** register the new function ([465b759](https://github.com/tks18/pyquery/commit/465b759f60c5e833d7ab1787fd85739bfc486909))
* **backend/io:** robust conversion of encoding to utf8 in a streaming way ([aa15eb1](https://github.com/tks18/pyquery/commit/aa15eb1eb67f7dd22ca7fe4ab9c828070766c893))
* **backend/io:** robust detection of encodings incase of csv ([e294d8e](https://github.com/tks18/pyquery/commit/e294d8e4a1154891347e114c1e2440f959221b81))
* **backend/transforms:** columns: add_col - now use robust ast parsing for blocking unsafe eval ([8757b16](https://github.com/tks18/pyquery/commit/8757b166cb761df3589449bb4920fd31de167f1e))
* **backend/transforms:** introduce new transform: advanced custom py script on the lazyframes ([bf6aab3](https://github.com/tks18/pyquery/commit/bf6aab337d9841a9b60967ee3170838f673d9917))
* **core/models:** add a new param model custom py script ([abc43db](https://github.com/tks18/pyquery/commit/abc43dba05a7120fe782956e2b047ae3d1594807))
* **core/models:** update the add col params to include a small default boilerplate code ([3fb3a19](https://github.com/tks18/pyquery/commit/3fb3a1949f67d363842abf906ad7e6481ccc2d28))
* **frontend/components:** eda: use the new sql code editor with auto completions ([7a94605](https://github.com/tks18/pyquery/commit/7a9460533dc26c01ae2739f91215194ae4db41da))
* **frontend/components:** editor: create 2 new editors based on custom editor - python & sql ([985392d](https://github.com/tks18/pyquery/commit/985392d803a445f8f0339483cd104c368e374b73))
* **frontend/components:** file loader: warning - blazing fast ui update ([d1c7552](https://github.com/tks18/pyquery/commit/d1c75525ebca3f8a85c435d9014b6ad5dfc68913))
* **frontend/components:** sql: use the new sql code editor ([f7e80e7](https://github.com/tks18/pyquery/commit/f7e80e75f42ccf2d151def07ebf656b2bc042535))
* **frontend/custom:** create custom component: code editor based on react-ace and ace-builds ([a470591](https://github.com/tks18/pyquery/commit/a47059171affb172faa716ad8c326914a6d91b4c))
* **frontend/steps:** create a new renderer for custom script ([f74415c](https://github.com/tks18/pyquery/commit/f74415c869faf587ccf60edac134d175dd97553c))
* **frontend/steps:** register the new renderer ([bdb1c56](https://github.com/tks18/pyquery/commit/bdb1c560c368309aa4578cd7c8339b64d1c8e64c))
* **frontend/steps:** use the new code editor for add_new_col function ([719ecba](https://github.com/tks18/pyquery/commit/719ecba6c295cf85be7c204662c71a765bbd6a68))
* **frontend/utils:** create utils for completions for both python and sql ([cc19162](https://github.com/tks18/pyquery/commit/cc19162f9785f0931436cb8ef1ff9836eb8e1946))


### Docs 📃

* **readme:** update readme ([e68b6a7](https://github.com/tks18/pyquery/commit/e68b6a7a7a20d791aad7f9d636f65330c2edf3f6))


### Others 🔧

* **pyversion:** update app to 2.5.0 ([e7f7945](https://github.com/tks18/pyquery/commit/e7f7945951425f86c05fdc0488ad50199298bd58))

## [2.4.0](https://github.com/tks18/pyquery/compare/v2.3.4...v2.4.0) (2026-01-13)


### Features 🔥

* **backend/core:** add additional metadata for LF length ([5cb61ed](https://github.com/tks18/pyquery/commit/5cb61edab34ee3100a4dcc2cff6805a0d4955f2f))
* **backend/core:** expose the encoding detection & conversion api ([e776710](https://github.com/tks18/pyquery/commit/e7767106852201b3e6c213fba4c8acf188d137d4))
* **backend/io:** allow backend api to perform csv encoding conversion to utf8 ([6882083](https://github.com/tks18/pyquery/commit/68820839f3b910a9388d8b7668af49ce0240ce15))
* **backend/io:** allow new option to clean headers on load ([c392650](https://github.com/tks18/pyquery/commit/c392650b70a28c449aa46bd1069071dd75c5f8a1))
* **backend/transforms:** add a new function to clean headers ([546857e](https://github.com/tks18/pyquery/commit/546857ed15af9a83aaf4708ce2eb69e4cb8fa7e5))
* **backend/transforms:** register the new function: clean_headers ([7587e9b](https://github.com/tks18/pyquery/commit/7587e9bb1731ca748ef9a538fb8d1a4d46fcbc98))
* **frontend/components:** api loader - refactor to separate module, also beautify it ([63fd90f](https://github.com/tks18/pyquery/commit/63fd90fefffcf1124d4928f7e203967b95551fdd))
* **frontend/components:** file loader - completely revamped, add option to fix csv encode, fix head ([cfa86d3](https://github.com/tks18/pyquery/commit/cfa86d3db82942088dfa334db89573bdd260b23e))
* **frontend/components:** loader: create utils for cache, also refactor the sql_loader ([b5857f4](https://github.com/tks18/pyquery/commit/b5857f42b7d899387bf27809dabd6294d2552d48))
* **frontend/components:** loader: remove loader as it is refactor to sub modules ([46fb5ba](https://github.com/tks18/pyquery/commit/46fb5ba10586d0d0ff6608776bc5cc84b5407401))
* **frontend/components:** sidebar: update to the new loader changes ([87cf30d](https://github.com/tks18/pyquery/commit/87cf30d77921a2d3bdc242690641f94f81e1474d))
* **frontend/steps:** create a renderer for clean_headers ([66080d3](https://github.com/tks18/pyquery/commit/66080d378f0a8320d86eca4a5e5c071c2559f0cb))
* **frontend/steps:** register the new function: clean_headers ([5006c96](https://github.com/tks18/pyquery/commit/5006c96e86d249e4d2220284342b0d2c86950897))
* **frontend/utils:** add cache utils for frontend loaders for fast render ([8f0d2c1](https://github.com/tks18/pyquery/commit/8f0d2c17892dfb424ce66ca9af4c82a0b00c04db))
* **models:** add model for clean_headers ([f7f2770](https://github.com/tks18/pyquery/commit/f7f2770379a0ad7e0028494a103655b3d617872c))


### Styling 🎨

* **frontend/components:** recipe-editor: add additional meta in the text ([004a232](https://github.com/tks18/pyquery/commit/004a232cea40c90547bc2547bea89d3848652b79))


### Others 🔧

* **pyversion:** update app to 2.4.0 ([224d0f0](https://github.com/tks18/pyquery/commit/224d0f0fe755424677f43a1b7cbe2ce7fe5d7d0a))

### [2.3.4](https://github.com/tks18/pyquery/compare/v2.3.3...v2.3.4) (2026-01-11)


### Code Refactoring 🖌

* **backend/core:** linter fixes and import refactors ([5eb3289](https://github.com/tks18/pyquery/commit/5eb32894e30b6c7b1e4d75bb45e45c94d4473627))
* **backend/io:** update io_plugins to use the new function signature ([ed4bf46](https://github.com/tks18/pyquery/commit/ed4bf46bca46a6b8fa8c6a555b6f983397f0941a))
* **frontend/components:** export:  linter fixes and import refactors ([462fa52](https://github.com/tks18/pyquery/commit/462fa52974df19996270d08bbe3e0fa6c7a01c9a))
* **frontend/components:** sql_tab: linter fixes and import refactors ([d900db1](https://github.com/tks18/pyquery/commit/d900db19610b9b8bdb5b4c223f44fdd24fa03575))


### Features 🔥

* **backend/core:** expose the api for advanced filtering of files ([aaa1485](https://github.com/tks18/pyquery/commit/aaa14850ce1ad45faec0e62c1c7d7c3658bf691f))
* **backend/io:** implement new advanced filtering approach for loading files ([4a77a0b](https://github.com/tks18/pyquery/commit/4a77a0b5e29d8f484331939aa9f9f5fccfe8acfa))
* **backend/io:** now backend supports loading multiple sheets of excel files at same time ([2e7fe99](https://github.com/tks18/pyquery/commit/2e7fe99dd3a5052c1e1408261e498994b00f1607))
* **frontend/components:** loaders: new module - which will handle all the modals for file handling ([eca7366](https://github.com/tks18/pyquery/commit/eca73662793a83fe0514d94a3e8c491f95bf4df1))
* **frontend/components:** sidebar: refactor completely to use the modal based loading dialogs ([def885b](https://github.com/tks18/pyquery/commit/def885beb66695ab6d0bd8af010f4a83515da37f))
* **models:** add new model for file filters and advanced regex based input filters ([d2e46a8](https://github.com/tks18/pyquery/commit/d2e46a833bbfae17ee5c8991ef0eb6bb9aabd7af))
* **models:** update io_params to include the type changes for excel sheet names ([c3bef48](https://github.com/tks18/pyquery/commit/c3bef486aa6d82f8e39dfdf256fa151abc705d4a))


### Docs 📃

* **readme:** update readme to reflect recent changes ([70cb3c0](https://github.com/tks18/pyquery/commit/70cb3c01199c7e04434f27c979c31fa862136068))


### Others 🔧

* **pyversion:** update app to 2.3.4 ([e219551](https://github.com/tks18/pyquery/commit/e2195518bed44bff395895b99140dc328440a82a))

### [2.3.3](https://github.com/tks18/pyquery/compare/v2.3.2...v2.3.3) (2026-01-10)


### Docs 📃

* **readme:** update readme ([023b069](https://github.com/tks18/pyquery/commit/023b06976ed5b828a3fcf765f951c83a80a244e9))


### Code Refactoring 🖌

* **backend/io_plugin:** update function signature for load_lazy_frame ([48672a7](https://github.com/tks18/pyquery/commit/48672a748d24c3c91d9b4ca5433b185b9588d751))


### Features 🔥

* **backend/core:** in case of folders and process individually, add option for users to export sep ([642d719](https://github.com/tks18/pyquery/commit/642d7192d3a35246092c933edead72535d8d0835))
* **backend/io:** add new functionality to add source metadata to the lazyframes if reqd ([0d7f527](https://github.com/tks18/pyquery/commit/0d7f52766067cccd6902f838a5380b69e543cdbf))
* **backend/io:** add new functionality to export worker to support list of lazyframes ([1007f26](https://github.com/tks18/pyquery/commit/1007f265140d7f164452ec4ac0f9d2377f49970c))
* **backend/io:** add source metadata to the metadata dict ([67a8491](https://github.com/tks18/pyquery/commit/67a8491f7ca918c7c3b467ea3823854d2d9134d8))
* **backend/jobs:** add more information related to export (also support export indiv.) ([bca3557](https://github.com/tks18/pyquery/commit/bca3557806deb58069bc745a38f986b84bb729db))
* **backend/transforms:** update add_row_number func to support different options ([a944b93](https://github.com/tks18/pyquery/commit/a944b93a118f1128345c4df478f43b7175760827))
* **backend/transforms:** update the promote_header function to include / exclude few cols ([19e6ec8](https://github.com/tks18/pyquery/commit/19e6ec84f8d929ab9a55ce2b4736dd9fabf4c9a4))
* **cli/branding:** update branding to be the global helper for all logging across all cli's ([a6bde21](https://github.com/tks18/pyquery/commit/a6bde214a3ecfcf2c71902c15f7f898290e3744a))
* **cli/headless:** update to add new functionalities, use new brand logger ([f38fd1b](https://github.com/tks18/pyquery/commit/f38fd1b60d91a5a6a221b6f60a0fdd8338abba32))
* **cli/interactive:** completely revamp the interactive cli to become more intelligent ([86dd42d](https://github.com/tks18/pyquery/commit/86dd42d9bfd7501613619def2b09db2900faee8d))
* **cli/interactive:** update interactive to use new brand logger, also add support for new funcs ([e8f0e41](https://github.com/tks18/pyquery/commit/e8f0e418807fc5676264e6eed99b605b96a37666))
* **cli/main:** use new brand logger, also add args for new functionalities ([fe849dc](https://github.com/tks18/pyquery/commit/fe849dc4c237f745e02e6b7ece7893bb43f69425))
* **core/models:** add metadata param for export job ([1d25f89](https://github.com/tks18/pyquery/commit/1d25f89e29f03c2d63cb3111b949176207c8ecd7))
* **frontend/components:** export: allow support for multi-export in case process_individual is on ([855ccf9](https://github.com/tks18/pyquery/commit/855ccf9c749fdd9e93fe47f0648b52a1b5226410))
* **frontend/components:** now export shows more information about the exported file ([26c91ea](https://github.com/tks18/pyquery/commit/26c91ea701a8369beffb0038868d8d275c039d2e))
* **frontend/components:** sidebar: add multiple functionalities ([c32bdf0](https://github.com/tks18/pyquery/commit/c32bdf00d634b4f2f1654b1c3eb172b9e9c0c121))
* **frontend/steps:** update row_number function to support new options and functionalities ([19e20a2](https://github.com/tks18/pyquery/commit/19e20a2f27f66c24865b5af6ff92f303af8d56b6))
* **frontend/steps:** update the promote header to include new options allowed ([3e2f0d0](https://github.com/tks18/pyquery/commit/3e2f0d040c1507b3fb4bf4771faf78ba9ced9caa))
* **frontend/utils:** update dynamic_ui renderer to support excluding few field names when rendering ([042337b](https://github.com/tks18/pyquery/commit/042337be566835f388b61de97421fbd8ea3e25d6))
* **models:** update add_row_number model to include different options ([1b5a93c](https://github.com/tks18/pyquery/commit/1b5a93c992a9442eb352da6b90874aaf8969873e))
* **models:** update io_params to include source_info param for input and export_individual for exp ([15e4626](https://github.com/tks18/pyquery/commit/15e46263ceadecec0cd4c3b9c9fa43b54fe7ff23))
* **models:** update promote_header model to include new options ([f4a9443](https://github.com/tks18/pyquery/commit/f4a94432e5d13b5158dedef69bd9f3cb0c605129))


### Styling 🎨

* **backend/io:** linter changes ([7520680](https://github.com/tks18/pyquery/commit/7520680d99b039bb0129f897e4060e0d455f37f7))
* **cli:** linter fix ([fc5ed42](https://github.com/tks18/pyquery/commit/fc5ed42f04d1503aa995e8394d47b0b6abd8547a))
* **frontend/steps:** linter formatting ([1839e26](https://github.com/tks18/pyquery/commit/1839e261329900d1497f67368051c6510fb7379a))


### Others 🔧

* **pyversion:** update app to 2.3.3 ([3f47502](https://github.com/tks18/pyquery/commit/3f475026d17e9db31364785c3744b643bf336b1c))

### [2.3.2](https://github.com/tks18/pyquery/compare/v2.3.1...v2.3.2) (2026-01-09)


### Build System 🏗

* add chardet package for fixing csv encoding issues ([4180530](https://github.com/tks18/pyquery/commit/4180530b773871c6e4bb1a5ca799e0d33c8f965d))


### Features 🔥

* **backend/io:** now the backend supports multiple csv encoding formats ([84b3791](https://github.com/tks18/pyquery/commit/84b3791828641992c220780e5311597ef0287839))
* **cli/branding:** update the branding to show a cool OS Like bootup sequence ([fa9cfed](https://github.com/tks18/pyquery/commit/fa9cfed55b995bd6eb93701593a6d1f74ca0736f))


### Docs 📃

* **readme:** update the vibes in the readme to reflect recent character changes ([f16ef11](https://github.com/tks18/pyquery/commit/f16ef11e5d676810589cddd0c10384b8ad11aa66))


### Others 🔧

* **pyversion:** update app to 2.3.2 ([1a4f050](https://github.com/tks18/pyquery/commit/1a4f05009c68c75a16b05d382bb9d256025a0045))

### [2.3.1](https://github.com/tks18/pyquery/compare/v2.3.0...v2.3.1) (2026-01-08)


### Features 🔥

* **cli:** add a branding module to showcase the tool name, tagline ([64d40aa](https://github.com/tks18/pyquery/commit/64d40aa1935e37b8932e7b0b8e30cde133103ace))


### Bug Fixes 🛠

* **cli:** gracefully shutdown instead of giving error to the user, insert branding ([c7c17bd](https://github.com/tks18/pyquery/commit/c7c17bdc46c734bb753fa64525a4630d13fdf567))
* **cli:** interactive: excel files not working previously due to no prompt for sheet names fixed ([5279307](https://github.com/tks18/pyquery/commit/527930753ed783230680dbb5fef8667caed97903))


### Others 🔧

* **pyversion:** update version to 2.3.1 ([1b76de6](https://github.com/tks18/pyquery/commit/1b76de65b722a72909439d3a8fc36a7cccf31e34))

## [2.3.0](https://github.com/tks18/pyquery/compare/v2.2.0...v2.3.0) (2026-01-07)


### Features 🔥

* **api:** fix api to use the new metadata format for adding the dataset to backend ([2b0dfec](https://github.com/tks18/pyquery/commit/2b0dfec250892d72f2f60e4d30626ca1980d3510))
* **backend/analysis:** create a new type inference module under analysis ([ad78f13](https://github.com/tks18/pyquery/commit/ad78f139c55cf4ceceaf740496c15b5f44b880d0))
* **backend/analysis:** create another module under analysis for joins ([b4fe44f](https://github.com/tks18/pyquery/commit/b4fe44fc74dc263775a3cbece4b5da45ccec9bed))
* **backend/core:** completely refactor the backend core to only act as a facade for all ops ([a628fa1](https://github.com/tks18/pyquery/commit/a628fa176b19d3f6b7c2fe39aafa5d53a470741d))
* **backend/core:** create a new materializer module to handle the storage helpers ([d02b564](https://github.com/tks18/pyquery/commit/d02b5642dd94b6be195511ba53126a4aa88a3692))
* **backend/engine:** create a new execution module inside processing ([ae017c3](https://github.com/tks18/pyquery/commit/ae017c3d800eb3e0056a36f170aa338770fe96ce))
* **cli/headless:** add support for exporting, importing all the available backend methods ([6bd0d4c](https://github.com/tks18/pyquery/commit/6bd0d4c9f0bf111bf9589f57a8ec83055098d270))
* **cli/interactive:** now cli interactive also supports all the funcs from backend ([ae65d9b](https://github.com/tks18/pyquery/commit/ae65d9bec346c5fa55541bb45df1715ee0db02db))
* **cli:** add support for all args in the main parser for cli ([fa71723](https://github.com/tks18/pyquery/commit/fa717234394450da3d24e8e010c798e65c237dab))
* **core:** add param for io to add option to process individual files separately ([1cc12c2](https://github.com/tks18/pyquery/commit/1cc12c25930da65a4bbd1e0c3a26a90f29b2e5c6))
* **core:** create a new model for holding metadata related to all the datasets ([60c01c3](https://github.com/tks18/pyquery/commit/60c01c353059ae7d6da4ba6d981c1b6829816d5a))
* **frontend/components:** eda: add option for the user to select the row limit ([c7f4c3a](https://github.com/tks18/pyquery/commit/c7f4c3a82b97c968fdf29bebf49c56af7f73f5bf))
* **frontend/components:** eda: add support for different methods of data strategy ([5abeaa2](https://github.com/tks18/pyquery/commit/5abeaa2737e5523073144ab61575525f7582c183))
* **frontend/components:** eda: use the new eda view from the backend for accessing all the data ([1bc5803](https://github.com/tks18/pyquery/commit/1bc5803e9d81f8dfa8f692ceab20b8817d7c33e0))
* **frontend/components:** recipe: refactor to use the new api, also add more info for user ([f8e4dd2](https://github.com/tks18/pyquery/commit/f8e4dd297af54f0d11c6fbf8853c9d6d1a0c598c))
* **frontend/components:** sidebar: add option to process individual files, robust recipe downloads ([4679d56](https://github.com/tks18/pyquery/commit/4679d56df1b0dbf491008910bc3278bde0b7427c))


### Code Refactoring 🖌

* **backend/io:** refactor the io_plugin and util to a common io folder ([cc20b5a](https://github.com/tks18/pyquery/commit/cc20b5a628ec7b5fd6e1340cd4e7f9e1d3ea1cfc))
* **backend/transforms:** refactor the transforms to processing folder ([96c5148](https://github.com/tks18/pyquery/commit/96c514838975a8dbca0911721ac7560a7bf7a3ef))
* **backend/transforms:** update the registry to use the new module path ([1da3d29](https://github.com/tks18/pyquery/commit/1da3d29866fc1d7949ab5d13a1516faa683c11f1))
* **frontend/app:** move the cleanup as part of the engine itself ([1633545](https://github.com/tks18/pyquery/commit/1633545f2572e3fb59d61dd7035d8b34692c0af5))
* **frontend/components:** sql: use the new api, also add more info to the user ([88ba86b](https://github.com/tks18/pyquery/commit/88ba86b34fa387582832004d2b99d93ef921d22c))


### Others 🔧

* **pyversion:** update app to version 2.3.0 ([c544613](https://github.com/tks18/pyquery/commit/c544613d595304d6a81ccdde725fd34e9b205178))

## [2.2.0](https://github.com/tks18/pyquery/compare/v2.1.0...v2.2.0) (2025-12-31)


### Bug Fixes 🛠

* **backend/transforms:** clean cast: sometimes boolean doest cast properly ([bbbc700](https://github.com/tks18/pyquery/commit/bbbc700abef4e44ba9ef6687ba0fe5729b6badc5))


### Styling 🎨

* **backend/analysis:** stats: minor styling changes ([2688b3d](https://github.com/tks18/pyquery/commit/2688b3d4f87bfe1c4cd4c501955262263f05a3df))


### Features 🔥

* **backend/analysis:** add sensitivity analysis and PDP ([a01e001](https://github.com/tks18/pyquery/commit/a01e001fccd3ca478870d1f93ff36acf3439e481))
* **backend/analysis:** enhance existing ml functions to give more information ([d1438f4](https://github.com/tks18/pyquery/commit/d1438f43c6f455fca3b84925ae76a9c80cc1fdd4))
* **backend/analysis:** stats: add more helper functions such as kde curve, normal dist plotting, ec ([7347b50](https://github.com/tks18/pyquery/commit/7347b5028eebddae8dc9fbd7ffd6ba8e03e91e02))
* **frontend/components:** eda: add another tab for group contrast metric ([5afa041](https://github.com/tks18/pyquery/commit/5afa0416d3abd4cb3cbcb7166ea97cd9a7a6dcb1))
* **frontend/components:** eda: completely rewrite ML tab based on the new engine changes ([d0de0c4](https://github.com/tks18/pyquery/commit/d0de0c4027108b67ce0835dfa5898ec3ce81c724))
* **frontend/components:** eda: completely rewrite plots module based on new engine changes ([465dade](https://github.com/tks18/pyquery/commit/465dade36fdfaeb99c540bbfde5ca0682deb75be))
* **frontend/components:** eda: core - use the new cached api for storing data, also tab reordering ([4ee1c7e](https://github.com/tks18/pyquery/commit/4ee1c7ef8bddfe076b9222d5143735f0e2161116))
* **frontend/components:** eda: implement caching across entire tab for faster processing ([2967179](https://github.com/tks18/pyquery/commit/2967179c505bd77343e2aade009549fe83ef24f8))
* **frontend/components:** eda: introduce new tab for advanced profiling ([502f190](https://github.com/tks18/pyquery/commit/502f190d8f83a81334e47322528a635c6534964f))
* **frontend/components:** eda: rewrite simulation tab with new functionalities from the engine ([794d2cf](https://github.com/tks18/pyquery/commit/794d2cfdfc94553b89d10fc671be70b3b55f69eb))


### Code Refactoring 🖌

* **frontend/components:** eda: use the cached df for processing ([24b8b21](https://github.com/tks18/pyquery/commit/24b8b21588410f6d476b858c038ac0c8b7455e7e))


### Docs 📃

* **readme:** update readme completely to give more detailed information about the tool ([158d54e](https://github.com/tks18/pyquery/commit/158d54ec8740fa0b31751ae01df7263ef63bbc24))


### Others 🔧

* **pyproject:** update app to version 2.2.0 ([696214f](https://github.com/tks18/pyquery/commit/696214f973b3f73b12029fa9cb0ac4ff7d21e156))

## [2.1.0](https://github.com/tks18/pyquery/compare/v2.0.2...v2.1.0) (2025-12-30)


### Bug Fixes 🛠

* **frontend/components:** recipe_editor: sometimes the updated schema doesnt propogate for next step ([c8c466c](https://github.com/tks18/pyquery/commit/c8c466c0b79974024d0a110612b24b523a609244))


### Build System 🏗

* **pyproject:** add scipy as dependency for build ([907c157](https://github.com/tks18/pyquery/commit/907c157a5732babbdecd519885b2620d88c91975))


### Code Refactoring 🖌

* **backend/core:** use the updated centralized staging function across all io ops ([d8a8386](https://github.com/tks18/pyquery/commit/d8a8386f9f661e02e89f3ba6cd1256b45371c82a))
* **frontend/app:** refactor the main entry point for eda tab ([e8ed1b5](https://github.com/tks18/pyquery/commit/e8ed1b5803c199c35315ebadeaaf8a77b69b3557))
* **frontend/components:** remove the old eda_tab file as it has been refactored completely ([ac8d415](https://github.com/tks18/pyquery/commit/ac8d415f50925f5a83a22542276a91bdc8c30e57))


### Features 🔥

* **backend/analysis:** create a centralized analysis class that will handle all analysis ops ([eddf6ed](https://github.com/tks18/pyquery/commit/eddf6ed56b6518b1a4fcb79c4e9b6b7c017be4b1))
* **backend/analysis:** create a new analysis engine in the backend ([588c6a0](https://github.com/tks18/pyquery/commit/588c6a05497e260107b355556e9ac319f271ce64))
* **backend/analysis:** create a new ML engine in the backend ([15b2fb9](https://github.com/tks18/pyquery/commit/15b2fb9e650549ef62fd5ca9e11b53368da06216))
* **backend/core:** expose the analysis engine through the api ([0ab8417](https://github.com/tks18/pyquery/commit/0ab8417170f72bfd70f8fbbaf7d09d03f8d1567a))
* **backend/core:** use the updated centralized staging dir for handling all intermediate saving ([b7a3a36](https://github.com/tks18/pyquery/commit/b7a3a36a7a2f1254cf74648762164471c9093542))
* **backend/core:** write a new function that will handle the centralized staging directory handling ([6d3c146](https://github.com/tks18/pyquery/commit/6d3c1467cc5367d08830a0a219c5ce9e4670faaa))
* **frontend/app:** add the cleanup program at start to clean all old staging files ([6298ac6](https://github.com/tks18/pyquery/commit/6298ac6c7a1b53207f152d9e28f88f8006905393))
* **frontend/components:** eda: create a new ML component for frontend ([3cb1ecb](https://github.com/tks18/pyquery/commit/3cb1ecb7d3b14d7766fb48e7dd71ce0209da7583))
* **frontend/components:** eda: create a overview component ([7131e63](https://github.com/tks18/pyquery/commit/7131e636b62eb5e40a5e924346abcbc025e743f8))
* **frontend/components:** eda: create a shared context for all components in EDA ([3d80abd](https://github.com/tks18/pyquery/commit/3d80abd74ae4a6b9163d456ebaf8ca5f91b436f4))
* **frontend/components:** eda: now orchestrate all the tabs using this start point ([35fbd12](https://github.com/tks18/pyquery/commit/35fbd12ca1403398643bd54abdaaf311042b1bdc))
* **frontend/components:** eda: write a new plots module which will have all the charting components ([075d3b2](https://github.com/tks18/pyquery/commit/075d3b2ecba1cbd1ebe1d2f84565aed50271db8f))
* **frontend/components:** eda: write a simulation tab component ([4d7b431](https://github.com/tks18/pyquery/commit/4d7b4316d3ad730eb2df61cbfbed612851b90e10))
* **frontend/components:** sidebar: add option for the user to do manual cleanup of staging folder ([a00bff4](https://github.com/tks18/pyquery/commit/a00bff456bdadae47ab737accad1adc4ee82ae68))
* **frontend/state:** update the state manager to hold states related to eda_tab (future update) ([42f6258](https://github.com/tks18/pyquery/commit/42f62589a7a21015f9fb3e3055e1f4f0892db19c))


### Styling 🎨

* **backend/core:** linter changes ([0cd0dde](https://github.com/tks18/pyquery/commit/0cd0dde8a8ebbe5fc8f05504b5e0a660b112ee8d))
* **frontend/components:** sidebar: just a import refactor ([65835f3](https://github.com/tks18/pyquery/commit/65835f3a8ca6fdb48f1d04889f2cbf43007c7a9f))


### Docs 📃

* **eda guide:** add a new eda guide file to the database ([a753137](https://github.com/tks18/pyquery/commit/a753137975d92748fb32d9acecdb6f5387d73f13))
* **readme:** update readme to reflect recent app changes ([5593d42](https://github.com/tks18/pyquery/commit/5593d427de4d72cc649a0fb0984467fc9f27b5a7))


### Others 🔧

* **pyproject:** update app version to 2.1.0 ([0a56244](https://github.com/tks18/pyquery/commit/0a562446e11f72b64672180f934aa6a844c7c286))

### [2.0.2](https://github.com/tks18/pyquery/compare/v2.0.1...v2.0.2) (2025-12-28)


### Bug Fixes 🛠

* **frontend/components:** eda tab - fix depreciation warnings ([f60fb2b](https://github.com/tks18/pyquery/commit/f60fb2b6489be33f8d9580c5019a6c912c19c4c7))


### Others 🔧

* **pyproject:** update app to v2.0.2 - fix eda tab depreciation warnings ([e433cfd](https://github.com/tks18/pyquery/commit/e433cfd67463b03e99c3305d515c1725f47b081a))

### [2.0.1](https://github.com/tks18/pyquery/compare/v2.0.0...v2.0.1) (2025-12-28)


### Bug Fixes 🛠

* **frontend/components:** eda tab becoming non-responsive ([0268365](https://github.com/tks18/pyquery/commit/0268365e3a67d886214bc67aaae9f09785d3f89c))


### Others 🔧

* **pyproject:** update project to v2.0.1 - critical fix for eda ([5601f37](https://github.com/tks18/pyquery/commit/5601f37a6631ad8eff138c167579fdba15038af4))

## [2.0.0](https://github.com/tks18/pyquery/compare/v1.3.0...v2.0.0) (2025-12-28)


### Styling 🎨

* change the name in the CLI ([fbf25e3](https://github.com/tks18/pyquery/commit/fbf25e3290aadb57153bf93740b161c9cd87c073))
* **frontend/components:** export.py newline due to linter ([9edbd10](https://github.com/tks18/pyquery/commit/9edbd1018f9db505bfe47a23aa53a10705f73924))
* **frontend:** state_manager.py whitespace change ([d849588](https://github.com/tks18/pyquery/commit/d849588fb4560cab61d962c1346460cd623b2ad3))


### Bug Fixes 🛠

* **api:** fix all type errors ([58c25fb](https://github.com/tks18/pyquery/commit/58c25fbabfcb0474fbbed437f9d8175d58d533aa))
* **backend/transforms:** previously it was creating new cols for all these changes, now corrected ([4ec7b3e](https://github.com/tks18/pyquery/commit/4ec7b3e1becae6805da337b7566cd07a1013a049))
* **backend:** fix all type errors ([c1d29e1](https://github.com/tks18/pyquery/commit/c1d29e1345ffb86a7d12be267c868d08db98eb0d))
* **cli:** fix all type errors ([25ad08c](https://github.com/tks18/pyquery/commit/25ad08cc879506f6e67dd978aea923afa25f5586))


### Build System 🏗

* **pyproject.toml:** add seaborn and matplotlib for upcoming feature: EDA ([a2096f3](https://github.com/tks18/pyquery/commit/a2096f3498119e6e096427e390ffee07b1cd1e7f))
* **pyproject:** add plotly, statsmodel, scikit-learn [future features] ([1165044](https://github.com/tks18/pyquery/commit/1165044058a1d07ff32f97783686f93e0aa24db4))
* **pyproject:** require python-multipart in the backend (FastAPI) for file handling ([080c49f](https://github.com/tks18/pyquery/commit/080c49f7ee1eca4d0e1343e2ac1c236f5f5b9b33))


### Features 🔥

* **backend/core:** add a function to materialize the dataset and load to the pipeline ([6bd3f1d](https://github.com/tks18/pyquery/commit/6bd3f1d1f21fded81197eee881693c9318b3a94e))
* **backend/core:** add a new function to analyze the join match / overlap ([58770ea](https://github.com/tks18/pyquery/commit/58770ea759d02c8a7f7a0486d0a5dcc19d1332e4))
* **backend/core:** allow custom SQL queries to be run on the loaded datasets (for powerusers) ([68772d1](https://github.com/tks18/pyquery/commit/68772d1966152d3242b9d7c3a1caa18185c31a16))
* **backend/core:** update get_schema to get the proper schema after applying the steps ([89d4388](https://github.com/tks18/pyquery/commit/89d4388ade7cf3b87cd0cb6119172605c4e0acb7))
* **backend/core:** update the sql engine to run after applying steps from recipe editor ([591c3c1](https://github.com/tks18/pyquery/commit/591c3c1bba9cdf8cd4fc72c3339856731ee021b4))
* **backend/core:** update the sql export to use the transformed data to run queries and export ([311ced7](https://github.com/tks18/pyquery/commit/311ced71603128ab642927c0634a8bd3d1cf1c7f))
* **backend/core:** write a new function for SQL preview (limit the rows then execute sql) ([ae0b48c](https://github.com/tks18/pyquery/commit/ae0b48cdd6ae34b8263e8f4900b65da39510e984))
* **backend/core:** write a new function to infer the types based on the sample rows selected ([2595b10](https://github.com/tks18/pyquery/commit/2595b10db128d2dcaa6b4de086f112b5150d7b62))
* **backend/engine:** access the api for getting sheet names through engine ([11f450b](https://github.com/tks18/pyquery/commit/11f450b5c11f877d4ac4e5aeb20eefcbbfb4f5df))
* **backend/engine:** make necessary changes as required by the loader funcs ([6b1d221](https://github.com/tks18/pyquery/commit/6b1d2219239866b64bffb615c5bbb88f78a97823))
* **backend/io:** excel: add option to get the sheet names [both folder/file] ([35b1306](https://github.com/tks18/pyquery/commit/35b1306bd3bc22fa75afc933d76650954e34aff7))
* **backend/jobs:** allow to pass a precomputed lf (for a upcoming feature related to SQL Queries ([92f703e](https://github.com/tks18/pyquery/commit/92f703e19ae81b8165a8a5531948dc6db6a8adc7))
* **backend/loaders:** allow passing tuple as return so that we can return metadata ([453b89e](https://github.com/tks18/pyquery/commit/453b89e90dd980e465478350f8ab158e7ffa3913))
* **frontend/components:** add a button to materialize the data and add to the pipeline ([21dfcf6](https://github.com/tks18/pyquery/commit/21dfcf6f5f02487db9543db73e9a7872c9a7c887))
* **frontend/components:** add a new tab for doing EDA on the datasets ([bcb88aa](https://github.com/tks18/pyquery/commit/bcb88aa5bc417ea54e68a6f56c90f2c073eb9d4b))
* **frontend/components:** add a new tab for running sql queries on the loaded dataset (poweruser) ([076bb0a](https://github.com/tks18/pyquery/commit/076bb0aeef0385298afa605a254fdedbf3a56fff))
* **frontend/components:** add option to maintain the queries history for sql ([8011720](https://github.com/tks18/pyquery/commit/801172067cd387b73e3ae6daff163bff8f901e90))
* **frontend/components:** add option to materialize the sql output as well to the pipeline ([39c0986](https://github.com/tks18/pyquery/commit/39c0986c2af99ce45c55b413e9e85a4c46ed5755))
* **frontend/components:** get quick profile on the sql query ran ([3572eb2](https://github.com/tks18/pyquery/commit/3572eb2d420126f4688e3646dc75d8157e78fa61))
* **frontend/components:** integrate the file / folder picker in the export component for better ux ([a23787e](https://github.com/tks18/pyquery/commit/a23787e6a09d1952e74cf52e5baa0878e3c96205))
* **frontend/components:** integrate the file & folder picker component in the sidebar for better ux ([8874ce7](https://github.com/tks18/pyquery/commit/8874ce7d1cc2017b071acb13cf122e8753685d93))
* **frontend/components:** revamp eda tab completely: ML kit, simulations, distributions, relations ([bb436bb](https://github.com/tks18/pyquery/commit/bb436bb9aa7e6f941727db0623fa0a63a2390025))
* **frontend/components:** sidebar: add a checkbox to detect the types when loading the dataset ([fb5277e](https://github.com/tks18/pyquery/commit/fb5277eef951813d3992fb77fcd8e4aeafac56cd))
* **frontend/components:** update recipe editor to support preview slicing ([16b2844](https://github.com/tks18/pyquery/commit/16b28443cb509d478ac871748829f4f1e13618f4))
* **frontend/components:** update recipe_editor page to incorporate undo, redo & params update ([8a1ae1e](https://github.com/tks18/pyquery/commit/8a1ae1e65334801cafe1f436eb7f4be9ffd4308b))
* **frontend/components:** update sidebar to add undo / redo buttongs ([26c4964](https://github.com/tks18/pyquery/commit/26c49640fcfb3bb17ed92527e264b44d9516e0da))
* **frontend/components:** update the sql_tab with updated schema and table explorer ([35d691f](https://github.com/tks18/pyquery/commit/35d691fb1ed8950a034153ce67c62d1344c1199c))
* **frontend/components:** use the update sql preview to get preview data ([d66bad8](https://github.com/tks18/pyquery/commit/d66bad809b7ebf898ad2d2af893a4f4c3e9bc54d))
* **frontend/steps:** write a new detect types feature in clean/cast types transforms ([675fcdd](https://github.com/tks18/pyquery/commit/675fcdd7a3defa995d5c36fe716f4c818edd2474))
* **frontend/transforms:** render the join analysis using the backend api, also minor refactors ([c524782](https://github.com/tks18/pyquery/commit/c5247825a18c192e3e198ec0d5247a6bface3936))
* **frontend:** add a new tab for EDA ([6916e68](https://github.com/tks18/pyquery/commit/6916e68f2cf43b0b641e99cf6ff0198b70a7ed02))
* **frontend:** add a new util to write a file & folder picker component using tkinter ([17a0f98](https://github.com/tks18/pyquery/commit/17a0f986ce597038be1325233a9f1d1f3412a693))
* **frontend:** auto detect the output path based on the source path using the metadata in the api ([436a8dd](https://github.com/tks18/pyquery/commit/436a8dd930ab502503412a4c02987a34f40be241))
* **frontend:** update state for future updates ([baa3e4d](https://github.com/tks18/pyquery/commit/baa3e4d75edc2128395d5616adb14cdbff15bf5c))
* **frontend:** update the state to maintain the undo and redo stack to go back and forth the steps ([21e130a](https://github.com/tks18/pyquery/commit/21e130a5dad784a9e0001093af685276cfbbc5ca))
* **frontend:** utilize the sheet name api from backend to increase ux for user ([8c36e88](https://github.com/tks18/pyquery/commit/8c36e88d44385800c3750c523c072e4506239636))


### Code Refactoring 🖌

* **backend/utils:** a simple refactor to handle all exceptions ([375d271](https://github.com/tks18/pyquery/commit/375d2719fd4efbfa4d3e4762111ed06167731528))
* **frontend/app:** minor refactors ([96df0b1](https://github.com/tks18/pyquery/commit/96df0b166c4310f09cba75021471cd2b8e5c16a6))
* **frontend/components:** minor refactors ([b59b2cc](https://github.com/tks18/pyquery/commit/b59b2cc7034e484e8ca0a69717134f81afc1c969))
* **frontend/components:** refactor sidebar.py ([e4d8518](https://github.com/tks18/pyquery/commit/e4d8518556a26111c56741cfcadfdfa495038a07))
* **frontend/components:** sql_tab.py minor refactoring, wording changes ([8c907a1](https://github.com/tks18/pyquery/commit/8c907a1a61ff602f7246482f10f4fdb5933bae4d))
* **frontend/components:** use the updated signature for exporting ([f24c435](https://github.com/tks18/pyquery/commit/f24c435dd5ca9886d51b0805cf6fbd40d996163f))


### Docs 📃

* **readme:** update readme ([c490c25](https://github.com/tks18/pyquery/commit/c490c2578a810a3bff620a281bc8c91affa1a364))
* **readme:** update readme completely to reflect new features ([050b213](https://github.com/tks18/pyquery/commit/050b21366cc42468fcc5b82e77d31bf390c1b2b3))
* **readme:** update the readme to incorporate the new changes ([bbf0601](https://github.com/tks18/pyquery/commit/bbf06013e6cc503362505dba7a36d18de3176401))


### Others 🔧

* **pyproject:** update version to 2.0.0 - improved SQL and new EDA Tab ([3e65abd](https://github.com/tks18/pyquery/commit/3e65abd69906018bba175333eed7cbd45f443c89))

## [1.3.0](https://github.com/tks18/pyquery/compare/v1.2.0...v1.3.0) (2025-12-24)


### Bug Fixes 🛠

* **backend:** fix the date/float/time/exceldate parsing logics to more robust parsing ([8381fae](https://github.com/tks18/pyquery/commit/8381fae0b2ba31af2142cee3f261b01033086b75))
* **backend:** use diagonal strategy for concat to handle schema changes (in case of xlsx) ([bf34cad](https://github.com/tks18/pyquery/commit/bf34cade617ca322e35812f97fdd6f3cc455a9c2))
* **cli:** fix all the bugs (export, transformations) in the interactive cli ([93cee84](https://github.com/tks18/pyquery/commit/93cee84c44bd85d48e393d81222ecbeafd22aa95))
* **transforms/combine:** join logic not taking updated schema for right -> fixed ([6da2b2e](https://github.com/tks18/pyquery/commit/6da2b2e3cdc81b4953558817dda664998202e63f))


### Features 🔥

* **api:** add a db module to track the api workflows ([2656128](https://github.com/tks18/pyquery/commit/26561284c848e3ea1a1bf5a12a33755c63822f8e))
* **api:** add a sample auth middleware for the api ([8e06a04](https://github.com/tks18/pyquery/commit/8e06a0441abe3a61ba3b0aaa41ecb69a9508043d))
* **api:** api/files -> new router point to start upload and download of files to the server ([56c9b28](https://github.com/tks18/pyquery/commit/56c9b28ca5cd85e9bad5ab67921c8d164ca12746))
* **api:** init db & add new route to the api /files ([14ef6e9](https://github.com/tks18/pyquery/commit/14ef6e910cdab65384244b0d6958261f6b6b25e7))
* **api:** now the recipes route will track all the changes through db ([51511a8](https://github.com/tks18/pyquery/commit/51511a87bb2027471b67312720a145ca0f7b6e78))
* **cli:** more robust headless cli ([64f7c1e](https://github.com/tks18/pyquery/commit/64f7c1e4151d69b73bfa4a45950ae3856f431595))
* **transforms:** add more cleaning transforms ([d8fa6f8](https://github.com/tks18/pyquery/commit/d8fa6f805094c613f4d50b8a86b08c489a6654b6))


### Code Refactoring 🖌

* **api:** minor refactoring ([64d2ddd](https://github.com/tks18/pyquery/commit/64d2ddde66a0593b5696b2d85ffa643b29391495))
* **backend:** orchestrate the entire modular engine and delete the old monolithic file ([99227b0](https://github.com/tks18/pyquery/commit/99227b006c46b9f2076e1d7d8fd4a814f4797a19))
* **backend:** refactor backend registration logic to seperate file (getting heavy) ([fc78579](https://github.com/tks18/pyquery/commit/fc7857923c942ae333f76e9fe79ed335beeed9fb))
* **backend:** refactor the engine execution logics to separate file ([0a79dba](https://github.com/tks18/pyquery/commit/0a79dbaa16b27b0f94f5506d4efd2ce52eec265d))
* **backend:** refactor the job management logic to separate file ([eaf642d](https://github.com/tks18/pyquery/commit/eaf642d4b234bc7a336d72b4a12bc9aee77c220b))
* **backend:** some minor refactors ([e9e57a1](https://github.com/tks18/pyquery/commit/e9e57a1b20ad29f6d4de32fe5dbea6fc64033674))
* **frontend/components:** update the params required for the new model ([24c2b91](https://github.com/tks18/pyquery/commit/24c2b91220809590bad9cf167cb8024055678ae9))
* **frontend:** minor refactoring changes ([a5eef41](https://github.com/tks18/pyquery/commit/a5eef41d40906ccb97cd5361ffd6c7990bcfcf52))
* minor refactor, folder shifts across all (cli, core, frontend) ([09b774a](https://github.com/tks18/pyquery/commit/09b774a4cd977a8ca2ca94cbebc711fb87dd0612))


### Build System 🏗

* **pyproject:** add fastexcel dependency (reqd by polars for excel processing) ([aaed764](https://github.com/tks18/pyquery/commit/aaed764167945899a9bc3fc9f54f5646f169baf7))


### Others 🔧

* **pyversion:** update app version to v1.3.0 ([55d10e6](https://github.com/tks18/pyquery/commit/55d10e6889b55db757c51035c4f12bc049274727))


### Docs 📃

* **readme:** update readme ([0b4cc2b](https://github.com/tks18/pyquery/commit/0b4cc2b95568b6a57d0fe55c94d57e4514d540fa))

## [1.2.0](https://github.com/tks18/pyquery/compare/v1.1.1...v1.2.0) (2025-12-22)


### Bug Fixes 🛠

* **app/cli:** fix wrong path for api making the api not start now fixed ([1324628](https://github.com/tks18/pyquery/commit/1324628977fff1f3467619a0a7ec3a128bb1d255))
* **backend/engine:** fix the duration of export not being sent to frontend ([be83939](https://github.com/tks18/pyquery/commit/be83939363a1d3577736c68d45e0c8969c5fd32d))
* **backend/engine:** fix the preview to create sample before applying any steps ([2b90007](https://github.com/tks18/pyquery/commit/2b900074fe6c584fe12365dd8b165c191c66a8ac))
* **backend/utils:** optimize all the robust parsers to utlize less compute ([808e19f](https://github.com/tks18/pyquery/commit/808e19f71ba8a4a6d823285e62859d9cd4d5da20))
* **frontend:** fix the duration not being shown when starting export ([44f59cd](https://github.com/tks18/pyquery/commit/44f59cd7e145373faf461ee2641c410324dd009a))


### Features 🔥

* **transforms:** add a function to concat / append another dataset ([a1d776f](https://github.com/tks18/pyquery/commit/a1d776ffeacaa6cd5a5af86caa44dcdbf1f03e26))
* **transforms:** add more advanced row operations - slice, drop, outliers ([ee8ce20](https://github.com/tks18/pyquery/commit/ee8ce20ed80ac16ff8cf2bdd3319130d8d75da7a))
* **transforms:** add more text cleaning functions - advanved regex, padd, etc ([761de3f](https://github.com/tks18/pyquery/commit/761de3f503b5e0b694589b84bfd4caa7c95e29c2))
* **transforms:** add new analytics -> skew & zscore ([ed744fa](https://github.com/tks18/pyquery/commit/ed744faf2d6302dba5180269d451851978bad5a1))
* **transforms:** add params for all the new functions ([bd5c2be](https://github.com/tks18/pyquery/commit/bd5c2be41c7597e57f326ae2f6588fc049943f09))
* **transforms:** allow more scientific math operations ([30f1a18](https://github.com/tks18/pyquery/commit/30f1a186f3ad9c59a2269b9b4db91b8fa3663d41))
* **transforms:** cast type: allow user to input the format types for date/time/datetime ([29a2a16](https://github.com/tks18/pyquery/commit/29a2a16ea395180804e3b6fc197801d1f1171448))
* **transforms:** register all the new functions in the backend & frontend ([02a72ea](https://github.com/tks18/pyquery/commit/02a72ea22cf3bc65ab8ab3c2b52147d09fbdd837))
* **transforms:** write advanced column functions such as promote headers, split col, etc, etc ([07efb06](https://github.com/tks18/pyquery/commit/07efb06157b6cf305f90c364677449aacc1f76a2))


### Others 🔧

* **pyversion:** update app to version 1.2.0 ([2194f7f](https://github.com/tks18/pyquery/commit/2194f7f43c9f5ff1cab417b188d4a8bc8bd2ac10))

### [1.1.1](https://github.com/tks18/pyquery/compare/v1.1.0...v1.1.1) (2025-12-21)


### Docs 📃

* **readme:** update readme.md ([f12e47b](https://github.com/tks18/pyquery/commit/f12e47be6f3163211f5b854e08bab5d8974175e9))


### Bug Fixes 🛠

* fix the directory which made the project duplicate itself when building ([cb4c3e1](https://github.com/tks18/pyquery/commit/cb4c3e16a1fae12f5dff3915cb01d42db62afdb9))
* **frontend/recipe:** possible bug fix that didnt update the schema after each step ([e2dba0b](https://github.com/tks18/pyquery/commit/e2dba0b86ede5ca364b65149f3052ff05469acd2))


### Others 🔧

* update app version to v1.1.1 ([99c429d](https://github.com/tks18/pyquery/commit/99c429d410d173c33a708ed2cdf00c6ffe96468f))
* update version & changelog ([41c8541](https://github.com/tks18/pyquery/commit/41c85415202ad75492caeadaa9be28ae43761fb7))

## [1.1.0](https://github.com/tks18/pyquery/compare/v1.0.0...v1.1.0) (2025-12-21)

### Code Refactoring 🖌

- minor hiccup in the module name since its already taken in pypi ([8d226d1](https://github.com/tks18/pyquery/commit/8d226d1f004edc7285dada8097db167777c8b1d9))

### Others 🔧

- update pyversion to v1.0.1 ([1170969](https://github.com/tks18/pyquery/commit/1170969d653978b8e1fc6108c71812b13cb19059))

## [1.0.0](https://github.com/tks18/pyquery/compare/v0.5.0...v1.0.0) (2025-12-21)

### Code Refactoring 🖌

- **app:** completely refactor all files from src/\* to src/pyquery ([50fe1a0](https://github.com/tks18/pyquery/commit/50fe1a06f54a0db3cf94f294d9e1e312007c801a))

### Features 🔥

- **api:** write a new fastapi backend that will act as a headless RESTfull API ([bb7107a](https://github.com/tks18/pyquery/commit/bb7107ad6960917d25b4c942a9679c60a670a11c))
- **app/types:** completely decouple backend and frontend to be truly flexible ([16c1c1b](https://github.com/tks18/pyquery/commit/16c1c1b155a7ef8104f8b2602744d8f986b332c8))
- **app:** run the main cli entry point ([8dd20c4](https://github.com/tks18/pyquery/commit/8dd20c45e7b56e3257f07a26b5e094703f47bae0))
- **backend:** decouple IO as well from the frontend ([4aebc2b](https://github.com/tks18/pyquery/commit/4aebc2bae0834ae96c0983bb24d21735da7ab8ad))
- **cli:** finally orchestrate everything with the cli module so that app can be packaged ([8644930](https://github.com/tks18/pyquery/commit/8644930a417fb8886f0165aaf077d1039fe9f6d0))
- **frontend:** fix some default spacing & styles for the streamlit UI ([ade17f9](https://github.com/tks18/pyquery/commit/ade17f93dd0ffc6b35108d703d5366b7faa2bc46))

### Docs 📃

- **readme:** update the readme to add the new features ([b0ea3ef](https://github.com/tks18/pyquery/commit/b0ea3ef6bd94fee10a9a665edf5fc097d331b008))

### Build System 🏗

- add fastapi, connectorx and other metadata for the build ([e555dd1](https://github.com/tks18/pyquery/commit/e555dd1477a7bca30626467bada6dc7ac1c85ed6))
- add manifest file ([d96d9f1](https://github.com/tks18/pyquery/commit/d96d9f1e75b9666556efcac8bbb229b1708eb01d))

### Others 🔧

- **stable:** stable app update: v1.0.0 ([a54ff22](https://github.com/tks18/pyquery/commit/a54ff226d13dfbf0f88e527d59ef146c221daad8))

## [0.5.0](https://github.com/tks18/pyquery/compare/v0.4.0...v0.5.0) (2025-12-20)

### Build System 🏗

- **packages:** add pydantic for robust type system for the app ([300c395](https://github.com/tks18/pyquery/commit/300c39517feade8ec543e0d76068d29e14134d9c))

### Code Refactoring 🖌

- **backend/helpers:** refactor it to type the module in a robust way ([8345793](https://github.com/tks18/pyquery/commit/83457932792b40398ec349414ab37913dfb0088e))
- **backend/t'forms:** update the column transforms to use the new typing ([21ec6fc](https://github.com/tks18/pyquery/commit/21ec6fcd160a6388ad4acb35f030b2f7f57a59b4))
- **backend/t'forms:** update the row transforms to use the new typing ([8ead3a4](https://github.com/tks18/pyquery/commit/8ead3a4f95645b0dadef6d295a488cebb4157c32))
- **frontend/components:** reflect the recent changes ([86793a6](https://github.com/tks18/pyquery/commit/86793a6033d9554b35e42e38d22a302afa3ef8dc))
- **frontend/components:** update the sidebar to reflect the recent type changes ([39fb966](https://github.com/tks18/pyquery/commit/39fb9667c1a450d81a6a92e2b3c025cddbd1555e))
- **frontend/utils:** refactor the dynamic_ui to support the new typing ([700debd](https://github.com/tks18/pyquery/commit/700debdf23764e74ca5b7360762bafec8af7fed0))

### Features 🔥

- **backend/engine:** rewrite the entire engine from scratch ([bdbe234](https://github.com/tks18/pyquery/commit/bdbe23417c1cc04ffed15d61a5e4c9390a4079f4))
- **backend/io:** rewrite the io helper from scratch so that we load the data faster ([bb56d9e](https://github.com/tks18/pyquery/commit/bb56d9e4b22a15ef68f973227ffc008f92b5801c))
- **backend/io:** use the updated types for loading and support more types using the helpers ([8b44425](https://github.com/tks18/pyquery/commit/8b44425388adc641307e4fc750429153f89ef025))
- **backend/t'forms:** add a new analytics transform functions ([68549d2](https://github.com/tks18/pyquery/commit/68549d2f9573bb4bbd48add619687f8e9655328e))
- **backend/t'forms:** add a new cleaning transform functions ([815f436](https://github.com/tks18/pyquery/commit/815f436d7b0e15161982b9cef88f4db9400c66fd))
- **backend/t'forms:** add new scientific and data transform library ([9ee95fa](https://github.com/tks18/pyquery/commit/9ee95fa8f538db7a33a3d340f054534b1d3dc8b4))
- **backend/t'forms:** rewrite the combine from scratch to be more type proof and error prone ([a0f0a92](https://github.com/tks18/pyquery/commit/a0f0a92175dedce267654fbd1a1ff5ada568cf03))
- **frontend/components:** add a new metadata for the user which shows the file size of the export ([fe4844f](https://github.com/tks18/pyquery/commit/fe4844fd8fcbef3320f4549e1b35523e7584a8a0))
- **frontend/components:** rewrite the recipe_editor completely to reflect the recent changes ([8745b65](https://github.com/tks18/pyquery/commit/8745b652e1321b60589f159344069d06569fa767))
- **frontend/state:** rewrite the state_manager completely to reflect the recent changes ([e963d40](https://github.com/tks18/pyquery/commit/e963d40837d9de4943f3505b0a1a480bd35f6884))
- **frontend/steps:** write all the renderers for the different transform modules ([1ee16b0](https://github.com/tks18/pyquery/commit/1ee16b0f89367769bc4b8be0f04cc8b513518e94))
- **frontend:** create a new renderer function that will dynamically display the step related params ([57c5b7b](https://github.com/tks18/pyquery/commit/57c5b7b21ad8a633484782304a4d9aa72cdecec4))
- **types:** write a registry type for the transformations registrations and management ([7d74143](https://github.com/tks18/pyquery/commit/7d741438246dbeb5d297a5b7bcb4f9d8e39e95a8))
- **types:** write all core models required by the backend engine ([b6435d7](https://github.com/tks18/pyquery/commit/b6435d7c75a4fbb981d895525c3113544ccfd114))
- **types:** write all the io types required for input and export types ([9d5719f](https://github.com/tks18/pyquery/commit/9d5719fb979eada121a1a9ded38bb8e1a4b8c9a5))
- **types:** write all the types required for each transform step ([79d7e1f](https://github.com/tks18/pyquery/commit/79d7e1fe1eaefa677c3730bfd40f03abc4407c54))

### Docs 📃

- **readme:** update the readme to reflect the recent major changes ([9c4a093](https://github.com/tks18/pyquery/commit/9c4a093aacedaedacad713ab44d70a6e0118e677))

### Others 🔧

- chore [space] change ([02bbfcf](https://github.com/tks18/pyquery/commit/02bbfcf217091ad2aa4639d9346bc2b4e568b268))
- chore [space] change ([08d15d4](https://github.com/tks18/pyquery/commit/08d15d4664180aa1b34d24f6c73eb188a6bee261))
- chore changes ([3f40216](https://github.com/tks18/pyquery/commit/3f40216cacff2ccffe2d56e5f536181ceee8c5d3))
- **pyversion:** update the app version to v0.5.0 ([ddbf62f](https://github.com/tks18/pyquery/commit/ddbf62fb38f439c29cfc59640b018306f6a48888))

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
