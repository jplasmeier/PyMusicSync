# Documentation

Some extra documentation to keep things organized.

## Data Structures

### Library

The library is the representative object of one's Drive or USB music. Library is implemented by a custom class.

### Collection

The collection is a member of the Library class. Collection is implemented by a dictionary with:

* key: Artist Name (str)
* value: ArtistItem (ArtistItem)

### CollectionItem

CollectionItem is a base class for ArtistItem and AlbumItem.

### ArtistItem

ArtistItem extends CollectionItem and adds a member albums, a list for AlbumItems associated with that artist.

## The Cannery

The Cannery is where we manage caching by making liberal use of pickle.
Caching Library and Collection are basically the same thing. Actually, all Library really is is a thin wrapper around its collection.
So we just pickle the Library, since it has the etag member.
From this we can access cached artists and albums  with only one IO operation.

## Naming Conventions

Variable names should provide information about their type.
For an artist, we differentiate as such:

* artist_name -> the name of the artist, str
* artist_item -> ArtistItem object
* drive_artist -> GoogleDriveFile object


