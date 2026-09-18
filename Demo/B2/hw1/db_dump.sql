BEGIN TRANSACTION;
CREATE TABLE books (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           title VARCHAR(255) NOT NULL,
           author VARCHAR(255) NOT NULL
        );
INSERT INTO "books" VALUES(1,'Modern Operating Systems (rwQP)','Randal Bryant xbG');
INSERT INTO "books" VALUES(2,'Database Internals (twZd)','Ilya Grigorik gVw');
INSERT INTO "books" VALUES(3,'High Performance Browser Networking (HIwj)','Ilya Grigorik hdV');
INSERT INTO "books" VALUES(4,'Database Internals (aZfe)','Martin Kleppmann tVa');
INSERT INTO "books" VALUES(5,'High Performance Browser Networking (IXXB)','Randal Bryant zZC');
CREATE TABLE orders (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           price FLOAT NOT NULL,
           bid INTEGER NOT NULL,
           FOREIGN KEY (bid) REFERENCES books(id)
        );
INSERT INTO "orders" VALUES(1,109.26,2);
INSERT INTO "orders" VALUES(2,97.29,3);
INSERT INTO "orders" VALUES(3,53.64,3);
INSERT INTO "orders" VALUES(4,83.17,2);
INSERT INTO "orders" VALUES(5,89.62,1);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('books',5);
INSERT INTO "sqlite_sequence" VALUES('orders',5);
COMMIT;
