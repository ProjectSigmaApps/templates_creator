# templates_creator
A tool for creating meritTemplates in bulk from a formatted CSV. This tool was created using PySimpleGUI in order to enable quick and easy cross-platform use. You will need to have an active app on the Merit platform, as well as access to an organization. As well, the pipfile will allow for easy local environment configuration. 

## Usage
Once you have run the tool, the GUI will guide you through entering your `appId`, `appSecret`, `orgId`, and browsing for your CSV. Once submitted it will attempt to retreive an `orgAccessToken`. If the app has never linked with that Org, it will guide the user through linking the app with the org using their Merit account. If successful in retreiving the token, it will then be used to process the CSV. 

The tool will check when creating templates if the template already exists, based on the name of that template. If yes, the template will then have the fields indicated in that row of the CSV. When working to add a `fieldSetting` to the `meritTemplate`, the tool will check if that field already exists. If not, it will be created, if so, it will simply be used to apply the `fieldSetting`.

