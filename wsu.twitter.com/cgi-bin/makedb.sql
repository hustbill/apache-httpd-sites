-- sqlite3 wsu-twitter.db
-- sqlite> .read makedb.sql
-- sqlite> .exit
-- sudo chgrp www .
-- sudo chgrp www wsu-twitter.db 
-- chmod 664 wsu-twitter.db 
-- chmod 775 .

CREATE TABLE users (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(45),
  passwd_hash VARCHAR(45),
  session_token VARCHAR(45) DEFAULT "0");
INSERT INTO users (user_id, username, passwd_hash)
  VALUES(0, 'wcochran', '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8');

CREATE TABLE TWEETS (tweet_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  time_stamp DATE DEFAULT (datetime('now','localtime')),
  isdeleted INTEGER DEFAULT 0,
  tweet VARCHAR(200));
INSERT INTO tweets (user_id, tweet)
  VALUES (0, 'Welcome to the CS 458 Twitter Service');

