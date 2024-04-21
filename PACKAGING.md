# PACKAGING

## Getting started
**Common rules:**
- Don't submit applications already part of the official `apt` repository
- No beta, alpha or testing packages. Has to be a stable release
- No need to submit the `.deb` file, only the specification file. We will download it ourselves

## Specifications
The `package.toml` file is divided in various subcategories. Each category should be filled out, but the Assets category is optional and the data submitted there is used purely for the website. 
Technically speaking, only the source file is needed, but to have a better overview of the repository, having additional details about it would be nice. \
Fields marked by `*` are necessary, all the others are optional.

### Submitter
- ***name**: The name of the user submitting the package. Ideally the maintainer, else set the **is_maintainer** to false
- ***email**: The email to contact you in case of issues with your submission
- **website**: Your personal website, will be linked to your profile
- ***is_maintainer**: (Default = true) If you, as the submitter, are the maintainer of the project or not

### Package
- ***name**: Name of the package
- ***version**: Version of the package. Can't be beta, alpha or anything related to it, it has to be an official stable release.
- ***summary**: A short description of the app
- **description**: A longer more detailed description of the application. Will be formatted as a normal string, therefore can contain `\n` to break lines
- ***type**: Should be one of the following: Business, DeveloperTool, Education, Entertainment, Finance, Game, GraphicsAndDesign, HealthcareAndFitness, Lifestyle, Medical, Music, News, Photography, Productivity, Reference, SocialNetworking, Sports, Travel, Utility, Video, Weather.
- **website**: The website of the application. Can be completely different from the source and is only used for the website
- ***license**: The license under which the application is being distributed. Use the exact nomenclature from the [list of SPDX identifiers](https://spdx.org/licenses/)
- ***source**: Has to be a URL pointing to a `.deb` file. You can use the variables `$pname` and `$pversion` for the package name and the package version respectively.
- ***auto_update**: (Default = true) If set to true, we will check periodically (once a week) if there is a new release available and update this file and the entry in the repository. This only works on GitHub (for now)
- ***arch**: Select one of the possible architectures. You need to submit a file and package for each arch if there are multiple ones. The architecture can be: "x86_64", "armv7h" or "aarch64"
- ***signature**: The SHA256 signature of the submitted package to verify its integrity

### Assets
- **logo**: URL to a publicly hosted image, ideally of size 256x256, which represents the logo of the application
- **banner**: URL to a publicly hosted image, ideally of size 500x256, which represents the banner of the app.
