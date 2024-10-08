import os
import re
import csv
import song_handler

pattern = re.compile('(.*): ([^ ]+) (.*)')
song_data = dict()

sh = song_handler.SongHandler()
for song in sh.songs:
    song_data[f"{song.author} - {song.title}"] = [0, 0]

if os.path.isfile("song_log.txt"):
    with open("song_log.txt") as file:
        for line in file:
            if m := pattern.match(line):
                timestamp, type, name = m.group(1), m.group(2), m.group(3)
                if type == "Started":
                    song_data[name][0] += 1
                elif type == "Finished":
                    song_data[name][1] += 1

    with open('song_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        field = ["Song", "Times Played Fully", "Times Started but not Finished"]
        writer.writerow(field)
           
        for song in song_data:
            song_data[song][0] -= song_data[song][1]
            writer.writerow([song, song_data[song][1], song_data[song][0]])
