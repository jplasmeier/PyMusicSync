# Documentation

Some extra documentation to keep things organized.

## Data Structures

### Library

The library is the root object of one's Drive or USB media. Library is implemented by a custom class which is essentially a wrapper around the `collection` member which is a dictionary containing the media metadata.

This is implemented via the `MediaLibrary` class. This might be an abstract class. It is inherited by GoogleDriveMediaLibrary which takes the name of the folder to use as root to fill the collection for the new object. 

Libraries are initialized with a given location for the library to consume. 

### Collection

The collection is a member of the Library class. Collection is implemented by a dictionary with:

* key: Artist Name (str)
* value: ArtistItem (ArtistItem)

### CollectionItem

CollectionItem is a base class for ArtistItem and AlbumItem.

### ArtistItem

ArtistItem extends CollectionItem and adds a member albums, a list for AlbumItems associated with that artist.

## Naming Conventions

Variable names should provide information about their type.
For an artist, we differentiate as such:

* artist_name -> the name of the artist, str
* artist_item -> ArtistItem object
* drive_artist -> GoogleDriveFile object

## Abstract File Schema

This is planned for the future. 

We would like a flexible way to represent the structure of the media which you are syncing. The best way to do this will be through a tree syntax, where each node is either a parent or a leaf. Leaf nodes are folders which are considered atomic (e.g. albums). 

So my music collection follows this syntax:

`root -> artists (parents) -> albums (leaf)`

It is important to note that a leaf node need not itself be a leaf in terms of its actual contents. For example, an album may itself contain multiple subdirectories containing images or the first and second disc. 

## User Interface

How should the functionality of Mass Media Sync be exposed to the end user?

### Functionality

A short list of functionality:

Atomic:

* Recursively upload and download folder from Google Drive
* Bin folders on USB device
* Diff a Google Drive folder and a USB Device/local folder

Composite:

* Diff and upload/download (sync) Google Drive folder with USB 

### UI Specific Functionality

We will need a good way to pick a USB Device/location to sync to. Same goes for Google Drive folders. 

The MVP for this will be a config.json file containing device names and paths. The next level version would be an actually decent command line UI (nCurses?). The next level version of that would be an actual GUI using Qt or GTK+. 


