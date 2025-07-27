# Stout Plus Home Assistant Integration

This repository contains the **Stout Plus** custom integration for Home Assistant.  It exposes a number of entities for controlling and monitoring your Stout Plus boiler and room climate controller.

## Features

Once configured, the integration provides the following entities:

- **Climate** – Control the boiler and room heating targets and modes.
- **Sensors** – Monitor power consumption, water pressure and current room temperature.
- **Select** – Change boiler operating modes.
- **Time entities** – Set night and day periods for the boiler.

The integration polls your boiler every few seconds (defaults are defined in the source code) to keep Home Assistant updated with the latest values.

## Installation

1. Copy or clone this repository to your Home Assistant `custom_components` directory, preserving the folder structure (`custom_components/stout_plus`).  With HACS installed, you can alternatively add this GitHub repository as a **custom repository** of type **Integration**.
2. Restart Home Assistant to pick up the new component.
3. From the *Settings → Devices & Services* page, click **Add Integration**, search for **Stout Plus**, and follow the prompts.  You will need to supply the host name or IP address of your boiler's web interface.

## Configuration

The integration uses a config flow, so all configuration is performed through the Home Assistant UI.  After initial setup you can adjust the host address via the integration options.

## Requirements

The integration relies on the [httpx](https://www.python-httpx.org/) library, which is declared in the manifest.  Home Assistant will install this dependency automatically during setup.

## Support

This project is not affiliated with Stout.  Please open an issue in this repository if you encounter problems or wish to suggest improvements.