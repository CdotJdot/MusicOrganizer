import os
import shutil
from mp3_tagger import MP3File, VERSION_2, VERSION_BOTH
from difflib import SequenceMatcher

# VERY IMPORTANT: For any of these functions to work properly, you MUST 'Run as administrator' !!


def similar(a, b):
    """For avoiding redundancy when an album or artist name has a minor difference (ex.: capitalization)"""
    return SequenceMatcher(None, a, b).ratio()


def sanitize(original):
    """To be used for name changes that apply to both tag names and folder names."""
    new = original.strip('\n')
    new = new.rstrip('\x00')
    new = new.strip()
    new = new.replace(' X ', ' & ')     # Ex.: DJ Muggs X Bambu
    new = new.replace(' x ', ' & ')
    if new[len(new) - 3: len(new)] == '12"':    # Ex.: Keep It Going 12"
        print(new + " was changed to 'Single'.")
        return 'Single'
    return new


def sanitize_folder(original):
    """To be used for name changes that apply only to folder names, leavings tags untouched. This exists because
    folders have stricter naming requirements than tags do."""
    new = original.replace(':', ' -')
    new = new.replace(' / ', ' & ')     # Ex.: Change / Survival Warz 12"
    new = new.replace('/', ' - ')       # Ex.: The 18th Letter/The Book of Life
    new = new.replace('; ', ' &')       # Ex.: Cannibal Ox; El-P; Vast Aire
    new = new.replace('?', '')          # Ex.: MM..Food?
    new = new.replace('!', '')          # Ex.: Blackout!
    if new[0] == '"' and new[len(new) - 1] == '"':  # Ex.: "The Mouse & The Mask"
        new = new.strip('"')
    if new[len(new) - 1] == '.':        # Ex.: Remember When...
        new = new.rstrip('.')
    if original != new:
        print('Folder name change: ' + original + ' => ' + new)
    return new


def dict_fill_from_bulk_mp3s(dict_input, mp3_location):

    for song in os.listdir(mp3_location):

        print('Currently processing dictionary fill for: ' + song)

        if song.endswith(".mp3"):
            # Defining starting file location of MP3
            song_location = mp3_location + '\\' + song
            song_start = MP3File(song_location)
            song_start.set_version(VERSION_2)

            # Getting artist name and album name from MP3 tags
            artist_name = song_start.artist
            album_name = song_start.album

        else:
            print('This file is not an MP3! Moving on...')
            continue

        if artist_name == [] or album_name == []:
            print('This MP3 is missing necessary tags! Moving on...')
            continue

        # Otherwise goes on to add dictionary entries if artist or album is unique
        else:
            artist_check = False    # Resets variable that keeps track of whether artist entry already exists

            # Checks to see if this artist already exists in the dictionary
            for entry in dict_input:

                if similar(entry, artist_name) > 0.85:
                    print('There is already a dictionary entry for this artist.')
                    artist_check = True    # Variable is updated to represent artist being redundant for this song
                    artist_name = entry
                    break

            # If the artist entry already exists then...
            if artist_check:

                # Checks to see if the album for this artist already exists in the dictionary as well
                for entry in dict_input[artist_name]:

                    if similar(entry, album_name) > 0.85:
                        print("There is already a dictionary entry for this artist's album. Moving on...")
                        break

                # If none of the album names are redundant, a new album name entry is created
                album_name = sanitize(album_name)
                dict_input[artist_name].append(album_name)
                print('A new album entry has been created for this artist in the dictionary. Moving on...')

            # If neither artist entry or album entry exists, this creates both of them
            else:
                artist_name = sanitize(artist_name)
                album_name = sanitize(album_name)
                dict_input[artist_name] = [album_name]
                print('A new artist entry with a corresponding album has been created in the dictionary. Moving on...')

    return dict_input


def bulk_create_folders(dict_input, mp3_destination):

    for artist in dict_input:
        artist_folder = mp3_destination + '\\' + sanitize_folder(artist)

        for album in dict_input[artist]:
            print('Processing folder creation for: ' + artist + ' - ' + album)
            album_folder = artist_folder + '\\' + sanitize_folder(album)

            if os.path.isdir(album_folder):
                continue

            else:
                try:
                    os.makedirs(album_folder)
                    print('Successfully created folder for: ' + artist + ' - ' + album)

                # Will usually fail if illegal folder characters in name, need to improve sanitize function for this
                except:
                    print('Failed to create folder for: ' + artist + ' - ' + album)
                    continue


def dict_fill_from_folders(dict_input, folders_location):

    for artist_folder in os.listdir(folders_location):

        # Solves a strange niche issue
        if artist_folder == 'Desktop.ini':
            continue

        first_entry = True
        artist_path = folders_location + '\\' + artist_folder

        for album_folder in os.listdir(artist_path):

            if first_entry:
                first_entry = False
                dict_input[artist_folder] = [album_folder]

            else:
                dict_input[artist_folder].append(album_folder)

    return dict_input


def bulk_mp3_move(dict_input, mp3_origin, mp3_destination):

    missing_tags_location = mp3_destination + '\\' + 'Unsorted\\Missing Tags'

    for song in os.listdir(mp3_origin):

        print('Currently moving: ' + song)

        if not song.endswith(".mp3"):
            print('This file is not an MP3! Moving on...')
            continue

        else:
            # Defining starting file location of MP3
            song_location = mp3_origin + '\\' + song
            song_start = MP3File(song_location)
            song_start.set_version(VERSION_2)

            # Getting artist name and album name from MP3 tags
            artist_name = song_start.artist
            album_name = song_start.album

            # If MP3 contains no artist or album metadata, song is moved to 'Missing Tags' folder
            if artist_name == [] or album_name == []:

                if os.path.isdir(missing_tags_location):
                    shutil.move(song_location, missing_tags_location)

                else:
                    os.makedirs(missing_tags_location)
                    shutil.move(song_location, missing_tags_location)

            # Otherwise goes on to find correct folder to move MP3 to using dictionary of folders
            else:
                artist_name = sanitize(song_start.artist)
                album_name = sanitize(song_start.album)
                true_artist = ''
                true_album = ''
                artist_sim_high = 0.0
                album_sim_high = 0.0

                for artist_entry in dict_input:

                    if similar(artist_name, artist_entry) > artist_sim_high:
                        artist_sim_high = similar(artist_name, artist_entry)
                        true_artist = artist_entry

                for album_entry in dict_input[true_artist]:

                    if similar(album_name, album_entry) > album_sim_high:
                        album_sim_high = similar(album_name, album_entry)
                        true_album = album_entry

                end_path = mp3_destination + '\\' + sanitize_folder(true_artist) + '\\' + sanitize_folder(true_album)

                try:
                    shutil.move(song_location, end_path)
                    print(song + ' successfully moved to: ' + end_path + '.')

                except:
                    print(song + ' failed to move.')
                    continue


def text_export(dict_input):
    """Writes all album and artist names from a dictionary to a text file"""
    transfer = open('artists and albums.txt', 'w+')

    for entry in dict_input:
        fixed = str(dict_input[entry])
        transfer.write(str(entry))
        transfer.write(fixed + '\n')

    transfer.close()


def update_dict(dict_input, artist_name, album_name):

    for entry in dict_input:

        if entry == artist_name:

            for item in dict_input[artist_name]:

                if item == album_name:
                    return

            dict_input[artist_name].append(album_name)
            return

    dict_input[artist_name] = [album_name]


def individual_mp3_move(dict_input, mp3_origin, mp3_destination):

    """
    This function also updates MP3 tags to match the folders the MP3 is moved to.
    If the MP3 is completely untagged then this function will not produce a good tagging result for the MP3. It is okay
    if the MP3 is missing an artist, song name, and/or album tag. However, if it has no tagging data whatsoever then it
    will not work properly with the mp3_tagger saving.
    """

    for file in os.listdir(mp3_origin):

        print('----------------------------------------------------------------------------------------------------'
              '------------------------------')
        print('Currently processing: ')
        print(file)

        if not file.endswith(".mp3"):
            print('Not an MP3, moving onto next file.')
            continue

        # Defining starting file location of MP3
        song_location = mp3_origin + '\\' + file
        song_file = MP3File(song_location)
        song_file.set_version(VERSION_2)

        # Getting artist name and album name from MP3 tags
        artist_tag = sanitize(str(song_file.artist))
        album_tag = sanitize(str(song_file.album))
        true_title = song_file.song

        if song_file.song == []:
            true_title = input('This file has no song tag name, please input one.')

        if song_file.artist == []:
            artist_tag = input('This file has no artist tag name, please input one.')

        if song_file.album == []:
            album_tag = input('This file has no album tag name, please input one.')

        artist_sim_high = 0.0
        artist_closest = ''

        for entry in dict_input:

            if similar(entry, artist_tag) > artist_sim_high:
                artist_sim_high = similar(entry, artist_tag)
                artist_closest = entry

        print('The closest artist match in your library is: ' + artist_closest)
        print('The artist tag name for this file is: ' + artist_tag)
        r1 = input("Input 'y' to use this artist name, input 't' to use the MP3 tag name, or input a new name to "
                   "create a folder for instead.")

        if r1 == 'y':
            true_artist = artist_closest
            album_sim_high = 0.0
            album_closest = ''

            for item in dict_input[artist_closest]:

                if similar(item, album_tag) > album_sim_high:
                    album_sim_high = similar(item, album_tag)
                    album_closest = item

            print('The closest album match in your library is: ' + album_closest)
            print('The album tag name for this file is: ' + album_tag)
            r2 = input("Input 'y' to use this album name, input 't' to use the MP3 tag name, or input a new name to "
                       "create a folder for instead.")

            if r2 == 'y':
                true_album = album_closest
                new_location = mp3_destination + '\\' + artist_closest + '\\' + album_closest

            elif r2 == 't':
                true_album = album_tag
                new_location = mp3_destination + '\\' + artist_closest + '\\' + sanitize_folder(album_tag)

            else:
                true_album = r2
                new_location = mp3_destination + '\\' + artist_closest + '\\' + sanitize_folder(r2)

        elif r1 == 't':
            true_artist = artist_tag
            print('The album tag name for this file is: ' + album_tag)
            r3 = input("Input 't' again to use the MP3 album tag, otherwise input an album name to create a folder "
                       "for instead.")

            if r3 == 't':
                true_album = album_tag
                new_location = mp3_destination + '\\' + sanitize_folder(artist_tag) + '\\' + sanitize_folder(album_tag)

            else:
                true_album = r3
                new_location = mp3_destination + '\\' + sanitize_folder(artist_tag) + '\\' + sanitize_folder(r3)

        else:
            true_artist = r1
            print('The album tag name for this file is: ' + album_tag)
            r4 = input("Input 't' to use the MP3 album tag, otherwise input an album name to create a folder "
                       "for instead.")

            if r4 == 't':
                true_album = album_tag
                new_location = mp3_destination + '\\' + sanitize_folder(r1) + '\\' + sanitize_folder(album_tag)
                song_file.artist = r1
                song_file.save()

            else:
                true_album = r4
                new_location = mp3_destination + '\\' + sanitize_folder(r1) + '\\' + sanitize_folder(r4)

        # Saves MP3 tags so ensure that they match their corresponding folder names
        song_file.set_version(VERSION_BOTH)
        song_file.song = true_title
        song_file.artist = true_artist
        song_file.album = true_album
        song_file.save()

        # Moves MP3 to the determined folder, creates it if it does not already exist
        if os.path.isdir(new_location) is False:
            os.makedirs(new_location)

        shutil.move(song_location, new_location)
        update_dict(dict_input, true_artist, true_album)


def main():

    lib_dict = {}
    origin = 'D:\\My Music\\Unsorted\\Failed to Sort'
    destination = 'D:\\My Music'
    individual_mp3_move(dict_fill_from_folders(lib_dict, destination), origin, destination)


main()
