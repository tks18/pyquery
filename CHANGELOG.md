# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

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
