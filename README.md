# BBCF Sprite Editor

This tool aims to simplify the process of creating custom color palettes for BlazBlue: Central Fiction. 
Manual palette creation is fairly well documented by the community, but it can be a tedious process that 
involes a lot of effort. There also exists the BBCF Improvement Mod which allows for in-game palette editing, 
but unfortunately this mod does not seem to work well for everyone.

# Upcoming Functionality

* Tutorial entries for Copy, Paste, Discard, Restore All, Restore Character, Export, Import actions
* Sprite image content editing support - No ETA

# Known Issues

* Not all character sprite files are mapped out with human readable names (yet)
* If the user drag-selects a sprite in the HIP image list, there is an off-by-one error and the wrong sprite 
may be displayed under certain circumstances
* When importing palettes that feature a save name, that meta data is not properly processed which results in the user 
being prompted to choose a name for palettes that are already named
