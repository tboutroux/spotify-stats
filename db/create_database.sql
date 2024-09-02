CREATE DATABASE IF NOT EXISTS spotify_app;

CREATE TABLE IF NOT EXISTS artiste (
    id varchar(25) PRIMARY KEY,
    name varchar(100) NOT NULL,
    popularity int NOT NULL,
    photo varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS album (
    id varchar(25) PRIMARY KEY,
    name varchar(100) NOT NULL,
    release_date datetime NOT NULL,
    total_tracks int NOT NULL,
    popularity int NOT NULL,
    photo varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS artiste_album (
    artiste_id varchar(25) NOT NULL,
    album_id varchar(25) NOT NULL,
    PRIMARY KEY (artiste_id, album_id),
    FOREIGN KEY (artiste_id) REFERENCES artiste(id),
    FOREIGN KEY (album_id) REFERENCES album(id)
);

CREATE TABLE IF NOT EXISTS track (
    id varchar(25) PRIMARY KEY,
    name varchar(100) NOT NULL,
    duration_ms int NOT NULL,
    popularity int NOT NULL,
    release_date datetime NOT NULL,
    photo varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS artiste_track (
    artiste_id varchar(25) NOT NULL,
    track_id varchar(25) NOT NULL,
    PRIMARY KEY (artiste_id, track_id),
    FOREIGN KEY (artiste_id) REFERENCES artiste(id),
    FOREIGN KEY (track_id) REFERENCES track(id)
);

CREATE TABLE IF NOT EXISTS album_track (
    album_id varchar(25) NOT NULL,
    track_id varchar(25) NOT NULL,
    PRIMARY KEY (album_id, track_id),
    FOREIGN KEY (album_id) REFERENCES album(id),
    FOREIGN KEY (track_id) REFERENCES track(id)
);

CREATE TABLE IF NOT EXISTS genre (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS artiste_genre (
    artiste_id varchar(25) NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (artiste_id, genre_id),
    FOREIGN KEY (artiste_id) REFERENCES artiste(id),
    FOREIGN KEY (genre_id) REFERENCES genre(id)
);

-- TEST

INSERT INTO artiste (id, name, popularity, photo) VALUES ('1', 'Ariana Grande', 100, 'https://i.scdn.co/image/ab67616d0000b273f3f3f3f3f3f3f3f3f3f3f3f3');