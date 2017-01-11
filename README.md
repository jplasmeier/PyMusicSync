# Google Drive Music Sync

### A sync utility for Google Drive and your USB Devices

Ideally, you have a bunch of files on Google Drive, and you want to sync them to a USB Device. The current Google Drive client for Mac does not support this- probably for good reason.
Google Drive's provided utility is aimed at replicating files that change with your Drive. For example, your My Documents folder might as well be a Google Drive folder.

However, media files are generally read-only. This tool is meant to augment the official Google tool when you have a tiny laptop and a large USB device.

This software is in alpha and may not work as expected!

### Modes and Options

There are a few different modes and options that Mass Media Sync supports.

#### Modes:

|Name|Usage|Definition|
|----|-----|----------|
|One Way|one-way drive usb|drive = drive, usb = drive ∪ usb|
|One Way w/ delete|one-way drive usb -d|drive = drive, usb = drive|
|Two Way|two-way drive usb|drive = drive ∪ usb, usb = drive ∪ usb|
|Two Way w/ delete|two-way drive usb -d|drive = drive ∩ usb, usb = drive ∩ usb|

**One Way**

Add the contents of one device to the other.

**One Way w/ Delete**

Replace the contents of one device with the other.

**Two Way**

Combine the contents of each device onto each device.

**Two Way w/ Delete**

Remove any content not on all devices from all devices. 


#### Options:

|Name|Usage|Description|
|----|-----|-----------|
|Delete|-d, --delete|Deletes "extra" files. Behavior depends on the mode. See above.|
|Cache|-c, --cache|Caches any Drive libraries being synced. WARNING: any changes to cached drive libraries made through the standard Google Drive client **will not** be reflected upon sync! Use with caution.
|Clean Unicode|--clean-unicode|Some Unicode strings cause issues with creating directories. This will go through and set all file/folder names to their "clean" equivalent.|

### Running PyMusicSync

* Install requirements from requirements.txt
* python music\_sync/music\_sync.py

Currently the Google Drive folder containing your files is hardcoded so you probably want to change it.
The directory structure is hard coded as well. I'm working on fixing this eventually to be more abstract.

### License: MIT License
