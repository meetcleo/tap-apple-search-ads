# Apple Search Ads Singer Tap

[Singer.io](https://www.singer.io/) Tap for [Apple Search Ads](https://searchads.apple.com/) API. 

> [!NOTE]
> This tap was forked from [Mighty Digital's original version](https://github.com/mighty-digital/tap-apple-search-ads), to add support for the [ASA Impression Share Report](https://developer.apple.com/documentation/apple_search_ads/impression_share_reports). 


## Features

- Covers 3 endpoints - **Campaign**, **Campaign Level Reports**, and **Impression Share Reports**.
- Available streams offer formatting variations of objects from given endpoints - unstructured objects, flat objects.
- Supports [discovery mode](https://github.com/singer-io/getting-started/blob/master/docs/DISCOVERY_MODE.md#discovery-mode) and generates a proper Singer catalog.
- Streams that provide "flat" objects can be used directly with SQL database targets, such as [target-csv](https://github.com/singer-io/target-csv) or [pipelinewise-target-postgres](https://github.com/transferwise/pipelinewise-target-postgres).
- Streams that provide "raw" objects can be used with unstructured targets, such as [target-json](https://github.com/dvelardez/target-json).

## Installation

Ensure that [Python](https://www.python.org/downloads/) is installed. The minimum required version is Python 3.8.

Tap is available only on the Cleo private PyPI repository, hosted on AWS CodeArtifact. The tap can be installed using `pip install tap-apple-search-ads` but local configuration is required to authenticate to the private repo. Talk to platform or AE team member to get setup. For local development you can clone this repo, and then install in editable mode:

```bash
git clone https://github.com/meetcleo/tap-apple-search-ads
pip install './tap-apple-search-ads'
tap-apple-search-ads --config config.json --discover > catalog.json
```

## Usage

To use the Tap, you need to create the `config.json` file with the values required to access the [Apple Search Ads API](https://developer.apple.com/documentation/apple_search_ads).

### Creating the config.json file

To access the Search Ads API you need to create a Public and Private Key pair and upload the Public Key to the Search Ads UI.

If you already have the Public Key uploaded, use the `clientId, teamId, keyId` values associated with the existing key.

If not, follow the steps outlined in [Implementing OAuth for the Apple Search Ads API](https://developer.apple.com/documentation/apple_search_ads/implementing_oauth_for_the_apple_search_ads_api). Complete the "Invite Users", "Generate a Private Key", "Extract a Public Key", "Upload a Public Key" steps to obtain the `clientId, teamId, keyId` values.

To generate the Private and Public Key pair you need to have the `openssl` program installed and configured to complete the steps. `openssl` program is usually already installed in most Linux distributions by default. In Windows, you can either use the `openssl` program provided with [Git for Windows](https://gitforwindows.org/) or [Miniconda/Anaconda](https://docs.conda.io/en/latest/miniconda.html) (or similar) or get the binary from the [OpenSSL](https://wiki.openssl.org/index.php/Binaries).

`config.json` values required for Apple Search Ads API:

- `org_id: string or integer` - Apple Search Ads Organization ID, obtained from Apple Search Ads console.
- `client_id: string` - obtained from "Implementing OAuth for the Apple Search Ads API".
- `key_id: string` - obtained from "Implementing OAuth for the Apple Search Ads API".
- `team_id: string` - obtained from "Implementing OAuth for the Apple Search Ads API".
- `private_key_file: string` - path to the `private-key.pem` file obtained from "Implementing OAuth for the Apple Search Ads API".
- `private_key_value: string` - contents of the `private-key.pem` file as string (joined with `\n` character).

You only need one of the private key values (`private_key_file` or `private_key_value`) in the `config.json` file.

After creating the `config.json` file and filling it with the relevant values, proceed to the **Discovery** step.

### Discovery

The first step of the actual Tap usage is the Discovery:

```bash
tap-apple-search-ads --config config.json --discover > catalog.json
```

This command will create the `catalog.json` file in the current working directory. This file contains descriptions of the available streams and their metadata. By default, every stream metadata consists only of the selection marker, and every stream is NOT selected by default. You need to alter the default `catalog.json` to enable the stream for syncing. Locate the relevant stream object in the `catalog.json`, then locate the `metadata` array inside the stream object, then locate the object with `"breadcrumb": []` and set the `"selected"` value of the object to `true`.

Currently, per-field metadata is not used, only whole streams can be enabled or disabled.

After creating the `catalog.json` file and selecting desired streams in the file, proceed to the **Sync** step.

### Sync

> [!IMPORTANT]
> To ensure a stream in the catalog is synced when you run the below command, you need to enable it. Modify the `selected` flag in the catalog.json for the stream you want to enable. 

Running the Tap with the `--catalog` option will enable the Sync mode. Sync mode extracts data from the tap, and prints it out to STDOUT, according to the [Singer spec](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md). 

```bash
tap-apple-search-ads --config config.json --catalog catalog.json
```

This command will output the Singer messages to the STDOUT. The output of the command can be piped directly into the Singer Targets.


## Development

To work on the Tap development, install additional dependencies from the `setup.cfg` file. Possible contributions:

- Adding additional API Endpoints and corresponding Streams.
- Adding more Singer metadata - per-field metadata parsing and usage.

### Installation for development

```bash
git clone https://github.com/meetcleo/tap-apple-search-ads

python -m venv venv
source venv/bin/activate

pip install '/tap-apple-search-ads[dev,test]'
```

### pre-commit

This project uses [pre-commit](pre-commit.com). Run `pre-commit install` to install pre-commit into your git hooks. pre-commit will now run on every commit. Running `pre-commit install` should always be the first thing you do.
