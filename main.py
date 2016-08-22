from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def list_folder(folder_id):
    # folder_id: GoogleDriveFile['id']
    _q = {'q': "'{}' in parents and trashed=false".format(folder_id)}
    return drive.ListFile(_q).GetList()

def get_artist_size(artist):
    albums = list_folder(artist['id'])
    size = 0
    for album in albums:
        album_size = get_album_size(album)
        if album_size is not None:
            size += album_size
    return size 

def get_album_size(album):
    tracks = list_folder(album['id'])
    size = 0
    for track in tracks:
        file_size = int(track["quotaBytesUsed"])
        if file_size is not None:
            size += file_size
    return size

gauth = GoogleAuth()
# Try to load saved client credentials
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)

size = 0
file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
for file1 in file_list:
    if file1['title'] == 'Music':
        artists = list_folder(file1['id'])
        i = 0.0
        for artist in artists:
            print (i/len(artists))
            i += 1
            size += get_artist_size(artist)

print("Your music takes up {0} Kib, {1} Gb of space.".format(size/1024/1024,size/1000/1000/1000)) 
