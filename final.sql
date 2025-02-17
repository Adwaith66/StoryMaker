CREATE DATABASE IF NOT EXISTS storyapp;


USE storyapp;


DROP TABLE IF EXISTS jobs;


CREATE TABLE jobs
(
    jobid       int not null AUTO_INCREMENT,
    jobname     varchar(64) not null,
	jobUUID     varchar(64) not null,
    status      varchar(64) not null,
    PRIMARY KEY  (jobid),
    UNIQUE      (jobUUID)
);


ALTER TABLE jobs AUTO_INCREMENT = 1001;  -- starting value


CREATE TABLE images
(
    imageid          int not null AUTO_INCREMENT,
    jobid            int not null,
    imageindex       int not null,  
	imageUUID         varchar(256) not null,  
	status            varchar(256) not null, 
    PRIMARY KEY (imageid),
    FOREIGN KEY (jobid) REFERENCES jobs(jobid),
	UNIQUE      (imageUUID)
);


ALTER TABLE images AUTO_INCREMENT = 1001;  -- starting value




-- INSERT INTO users(username, pwdhash)  -- pwd = abc123!!
--             values('p_sarkar', '$2y$10$/8B5evVyaHF.hxVx0i6dUe2JpW89EZno/VISnsiD1xSh6ZQsNMtXK');


-- INSERT INTO users(username, pwdhash)  -- pwd = abc456!!
--             values('e_ricci', '$2y$10$F.FBSF4zlas/RpHAxqsuF.YbryKNr53AcKBR3CbP2KsgZyMxOI2z2');


-- INSERT INTO users(username, pwdhash)  -- pwd = abc789!!
--             values('l_chen', '$2y$10$GmIzRsGKP7bd9MqH.mErmuKvZQ013kPfkKbeUAHxar5bn1vu9.sdK');


-- --
-- -- creating user accounts for database access:
-- --
-- -- ref: https://dev.mysql.com/doc/refman/8.0/en/create-user.html
-- --


DROP USER IF EXISTS 'storyapp-read-only';
DROP USER IF EXISTS 'storyapp-read-write';


CREATE USER 'storyapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'storyapp-read-write' IDENTIFIED BY 'def456!!';


GRANT SELECT, SHOW VIEW ON storyapp.* 
      TO 'storyapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON storyapp.* 
      TO 'storyapp-read-write';
      
FLUSH PRIVILEGES;


--
-- done
--


