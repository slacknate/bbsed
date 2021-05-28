# BBCF Sprite Editor

The foremost goal of the project is to streamline the process of creating custom color palettes 
for BlazBlue: Central Fiction. Manual palette creation is fairly well documented by the community, but it can 
be a tedious process that involves a lot of effort. There also exists the BBCF Improvement Mod which allows for 
in-game palette editing, but unfortunately this mod does not seem to work well for everyone.

The tool also aims to provide a means to share palettes with others so we can all view and admire each others 
creative work and appreciate it within the game easily and quickly.

# Upcoming Functionality

* Tutorial entries for Copy, Paste, Discard, Restore All, Restore Character, Export, Import actions
* Sprite image content editing support - No ETA

# Known Issues

* Not all character sprite files are mapped out with human readable names (yet)
* Palette Data, Zoom, and extra character control dialog positions are not file saved, and thus reset each time 
they are hidden/shown
* If the user drag-selects a sprite in the HIP image list, there is an off-by-one error and the wrong sprite 
may be displayed under certain circumstances
* When importing palettes that feature a save name, that meta data is not properly processed which results in the user 
being prompted to choose a name for palettes that are already named

# Shoutouts

Huge thanks to Dantarion and contributors for the repo [bbtools](https://github.com/dantarion/bbtools). 
Without it this project would not be possible. 
