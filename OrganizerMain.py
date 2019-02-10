import os
import shutil
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from difflib import SequenceMatcher


# Creating function that will determine if artist or album already has near identical entry
def similar(a, b):

    return SequenceMatcher(None, a, b).ratio()


def sanitize(original):

    new = original.rstrip('\x00')
    new = new.replace(':', ' -')
    new = new.strip('\n')
    return new


def fill_dictionary(dict_input):

    artist_name = []
    album_name = []

    for song in os.listdir('D:\\Holding'):

        print('Currently creating entry for: ' + song)

        if song.endswith(".mp3"):   # fix this with else continue
            # Defining starting file location of song
            song_location = 'D:\\Holding\\' + song
            song_start = MP3File(song_location)
            song_start.set_version(VERSION_2)

            # Getting artist name and album name from song tags
            artist_name = song_start.artist
            album_name = song_start.album

        # If song contains no artist or album metadata, script moves onto next song
        if artist_name == [] or album_name == []:
            continue

        # Otherwise goes on to add dictionary entries if artist or album is unique
        else:
            artist_check = 0    # Resets variable that keeps track of whether artist entry already exists

            # Determines if an artist name entry with a very similar name already exists in the dictionary
            # If that entry does exist, the script moves onto checking if the album name is unique
            for entry in dict_input:

                if similar(entry, artist_name) > 0.75:
                    artist_check = 1    # Variable is updated to represent artist being redundant for this song
                    artist_name = entry
                    break

                else:
                    continue

            # If the artist entry already exists then...
            if artist_check == 1:
                album_count = 0     # Keeps track of the number of album entries for the current artist

                for entry in dict_input[artist_name]:

                    # If album name is also redundant, moves onto next song
                    if similar(entry, album_name) > 0.75:
                        break

                    # Otherwise adds album entry to existing artist entry
                    else:
                        album_count += 1

                        if album_count == len(dict_input[artist_name]):
                            album_name = sanitize(album_name)
                            dict_input[artist_name].append(album_name)

                        else:
                            continue

            # If neither artist entry or album entry exists, this creates both of them
            else:
                artist_name = sanitize(artist_name)
                album_name = sanitize(album_name)
                dict_input[artist_name] = [album_name]

    return dict_input


def create_folders(created_dict):

    for artist in created_dict:
        print ('Processing directory for: ' + artist)
        artist_folder = 'D:\\My Music\\' + artist

        for album in created_dict[artist]:

            album_folder = artist_folder + '\\' + album

            if os.path.isdir(album_folder) is True:
                continue

            else:
                try:
                    os.makedirs(album_folder)

                except:
                    print(artist + ' failed to move.')
                    continue


def text_export(dict_input):

    # Writes all album and artist names to a text file
    transfer = open('artists and albums.txt', 'w+')

    for entry in dict_input:
        fixed = str(dict_input[entry])     # Need to change this to filter out junk text
        transfer.write(str(entry))
        transfer.write(fixed + '\n')

    transfer.close()


def mp3_mover(dict_input):

    for song in os.listdir('D:\\Holding'):

        print('Currently moving song: ' + song)

        if song.endswith(".mp3"):
            # Defining starting file location of song
            song_location = 'D:\\Holding\\' + song
            song_start = MP3File(song_location)
            song_start.set_version(VERSION_2)

            # Getting artist name and album name from song tags
            artist_name = song_start.artist
            album_name = song_start.album

            # If song contains no artist or album metadata, script moves onto next song
            if artist_name == [] or album_name == []:

                if os.path.isdir('D:\\My Music\\Unsorted') is True:
                    shutil.move(song_location, 'D:\\My Music\\Unsorted')
                    continue

                else:
                    os.makedirs('D:\\My Music\\Unsorted')
                    shutil.move(song_location, 'D:\\My Music\\Unsorted')
                    continue

            # Otherwise goes on to add dictionary entries if artist or album is unique
            else:
                artist_name = sanitize(song_start.artist)
                album_name = sanitize(song_start.album)
                true_artist = ''
                most_similar_artist = 0
                most_similar_album = 0

                for artist_entry in dict_input:

                    if similar(artist_name, artist_entry) > most_similar_artist:
                        most_similar_artist = similar(artist_name, artist_entry)
                        true_artist = artist_entry

                    else:
                        continue

                for album_entry in dict_input[true_artist]:

                    if similar(album_name, album_entry) > most_similar_album:
                        most_similar_album = similar(album_name, album_entry)
                        true_album = album_entry

                    else:
                        continue
                new_location = 'D:\\My Music\\' + true_artist + '\\' + true_album

                try:
                    shutil.move(song_location, new_location)

                except:
                    print(song + ' failed to move.')
                    continue

        else:
            continue


def main():

    artists_albums_dict = {}
    artists_albums_dict = fill_dictionary(artists_albums_dict)
    create_folders(artists_albums_dict)  # Dictionary to keep track of artist and album folders created
    mp3_mover(artists_albums_dict)


main()
