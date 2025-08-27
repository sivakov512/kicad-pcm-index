# KiCad PCM Repository

This repository contains Plugin and Content Manager (PCM) metadata for KiCad, providing an easy way to install KiCad Component Library and Template Collection.

## Available Packages

1. **KiCad Component Library** - Custom component library with symbols, footprints, 3D models and datasheets. [Repository](https://github.com/sivakov512/kicad-library)

2. **Espressif Library** - Official KiCad component libraries for Espressif SoCs and modules (ESP32, ESP8266, etc.). [Repository](https://github.com/espressif/kicad-libraries) - *Automatically updated daily*

3. **KiCad Template Collection** - KiCad templates optimized for PCB manufacturing services with preconfigured design rules and stackups. [Repository](https://github.com/sivakov512/kicad-templates)

## Automation

This repository includes automated workflows that monitor upstream libraries for new releases:

- **Espressif Library**: Checked daily at 10:00 AM UTC for new releases
- When new versions are detected, they are automatically added to the index
- Manual plugin additions are also supported through GitHub Actions workflows

## Installation

Follow these steps to add this repository to KiCad:

1. Open KiCad
2. Go to **Plugin and Content Manager** → **Manage**
3. Click **Add Repository**
4. Add this repository URL:
   ```
   https://raw.githubusercontent.com/sivakov512/kicad-pcm-index/master/repository.json
   ```
5. Click **OK**
6. Find the package you want to install in the list and click **Install**

## License

This repository is licensed under the MIT License - see the LICENSE file for details.

## Links

- [Component Library](https://github.com/sivakov512/kicad-library)
- [Espressif Library](https://github.com/espressif/kicad-libraries)
- [Template Collection](https://github.com/sivakov512/kicad-templates)
- [Issues and Feature Requests](https://github.com/sivakov512/kicad-pcm-index/issues)
