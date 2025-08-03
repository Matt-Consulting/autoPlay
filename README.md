# Dragon Warrior I Automation Project

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An experimental system that combines computer vision and machine learning to automate gameplay of Dragon Warrior I (NES) using the Mesen emulator.

![Project Overview](https://via.placeholder.com/800x400?text=Dragon+Warrior+Automation+Demo)  
*Screenshot placeholder - actual gameplay analysis will be shown here*

## Table of Contents
- [Features](#features)
- [Technical Architecture](#technical-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development Roadmap](#development-roadmap)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

### Core Capabilities
- Real-time game state analysis via screen capture
- 15×15 grid-based environment mapping
- Color-based object recognition (105+ types defined)
- Interactive debugging overlays (RGB values, type annotations)
- Automatic emulator window detection

### Planned Features
- Automated movement and combat systems
- Pathfinding algorithms for dungeon navigation
- Machine learning for adaptive gameplay

## Technical Architecture

### Component Structure
```
autoPlay/
├── main.py              # Main application controller
├── sense.py             # Computer vision and screen analysis
├── act.py               # (Planned) Input automation
├── think.py             # (Planned) Decision engine
├── type_mappings.json   # 105+ color-to-type mappings
├── MesenConfig.json     # Emulator controller bindings
└── README.md            # This documentation
```

### Technology Stack
| Component          | Technology Used         |
|--------------------|-------------------------|
| Screen Capture     | MSS + OpenCV           |
| Window Management  | xdotool (Linux)        |
| Emulator Control   | Mesen-S                |
| Core Processing    | Python 3.8+            |

## Installation

### Prerequisites
- Linux system (or WSL on Windows)
- Mesen-S emulator ([Download](https://www.mesen.ca/))
- Dragon Warrior I ROM (must be named `DragonWarrior.zip`)

### Setup Instructions
1. Install system dependencies:
   ```bash
   sudo apt update && sudo apt install -y xdotool python3-pip
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/Matt-Consulting/autoPlay.git
   cd autoPlay
   ```

3. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   *Example requirements.txt:*
   ```text
   opencv-python
   mss
   numpy
   ```

4. Configure your environment:
   - Place Mesen AppImage in project root
   - Add your ROM as `DragonWarrior.zip`

## Usage

### Basic Operation
```bash
python main.py
```

### Interactive Controls
| Key Binding | Function                      |
|-------------|-------------------------------|
| `q`         | Quit application              |
| `g`         | Toggle grid overlay           |
| `r`         | Toggle RGB value display      |
| `t`         | Toggle type annotations       |

### Sensing
Determing the state of the screen is done through sense.py.  This includes operations related to capturing the screen, dividing it into a grid, and then determing what types of tiles are displayed.
<img width="256" height="272" alt="StartScreen" src="https://github.com/user-attachments/assets/5ee4ef41-ad26-4bd3-bb42-b7bfe50062b1" />
<img width="370" height="331" alt="StartGrid" src="https://github.com/user-attachments/assets/775629f2-c4f2-489b-8736-f514e1bc2e24" />
<img width="645" height="700" alt="StartRGB" src="https://github.com/user-attachments/assets/e44c7918-7b17-4f35-a66c-5b947bb1c5e7" />


## Configuration

### Key Configuration Files
1. **type_mappings.json** - Define game object recognition:
   ```json
   {
     "color_to_type": {
       "132,132,132": 0,
       "40,47,96": 1
     },
     "type_aliases": {
       "0": "block",
       "1": "brick"
     }
   }
   ```

2. **MesenConfig.json** - Controller keybindings:
   ```json
   {
     "NES": {
       "Port1": {
         "Type": "NesController",
         "Mappings": {
           "A": 62,
           "B": 44
         }
       }
     }
   }
   ```

## Development Roadmap

### Current Focus
- Basic environment mapping
- Core computer vision pipeline
- Input/output system architecture

### Next Milestones
1. Pathfinding implementation
2. Combat automation framework
3. Expanded object recognition

### Long-Term Goals
- Machine learning integration
- Quest completion automation
- Performance optimization

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a Pull Request

## Troubleshooting

| Issue                  | Solution                                                                 |
|------------------------|--------------------------------------------------------------------------|
| Window not detected    | Check emulator window title matches exactly "Mesen - Dragon Warrior"     |
| Performance issues     | Reduce `sensor_refresh_rate` in Config class or disable debug overlays   |
| Color matching errors  | Adjust thresholds in `_match_color()` or add new mappings                |
| Capture problems       | Verify manual calibration values match your emulator window position     |

## License

MIT License - see [LICENSE](LICENSE) file for details.

*Note: Dragon Warrior is a registered trademark of Square Enix. This project is for educational purposes only.*
