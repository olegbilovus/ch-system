DROP TABLE IF EXISTS server CASCADE;
CREATE TABLE server
(
    ID   SMALLSERIAL PRIMARY KEY,
    name VARCHAR(20)
);

DROP TABLE IF EXISTS clan CASCADE;
CREATE TABLE clan
(
    ID       SERIAL PRIMARY KEY,
    name     VARCHAR(20),
    serverID SMALLSERIAL,
    FOREIGN KEY (serverID)
        REFERENCES server (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS userProfile CASCADE;
CREATE TABLE userProfile
(
    ID        BIGSERIAL PRIMARY KEY,
    name      VARCHAR(30),
    serverID  SMALLSERIAL,
    clanID    SERIAL,
    role      SMALLINT,
    hash_pw   VARCHAR(150),
    change_pw BOOLEAN,
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (serverID)
        REFERENCES server (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS apiKey CASCADE;
CREATE TABLE apiKey
(
    userProfileID BIGSERIAL PRIMARY KEY,
    key           VARCHAR(50) UNIQUE,
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS clanDiscord CASCADE;
CREATE TABLE clanDiscord
(
    clanID        SERIAL PRIMARY KEY,
    notifyWebhook VARCHAR(1000),
    discordGuildID VARCHAR(100),
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS timer CASCADE;
CREATE TABLE timer
(
    ID                 BIGSERIAL PRIMARY KEY,
    bossName           VARCHAR(50),
    type               VARCHAR(20),
    respawnTimeMinutes BIGINT NOT NULL,
    timer              TIMESTAMP WITHOUT TIME ZONE,
    clanID             SERIAL,
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP FUNCTION IF EXISTS timer_default();
CREATE FUNCTION timer_default() RETURNS trigger AS
$timer_default$
BEGIN
    IF NEW.timer IS NULL THEN
        NEW.timer = NOW() AT TIME ZONE ('UTC') + INTERVAL '1 MINUTE' * NEW.respawnTimeMinutes;
    END IF;
    RETURN NEW;
END;
$timer_default$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS timer_default ON timer;
CREATE TRIGGER timer_default
    BEFORE INSERT OR UPDATE
    ON timer
    FOR EACH ROW
EXECUTE PROCEDURE timer_default();

DROP FUNCTION IF EXISTS timer_minutes_remaining(timer TIMESTAMP WITHOUT TIME ZONE);
CREATE FUNCTION timer_minutes_remaining(timer TIMESTAMP WITHOUT TIME ZONE) RETURNS INTERVAL AS
$timer_minutes_remaining$
BEGIN
    RETURN timer - NOW() AT TIME ZONE ('UTC');
END;
$timer_minutes_remaining$ LANGUAGE plpgsql;

DROP TABLE IF EXISTS discordID CASCADE;
CREATE TABLE discordID
(
    userProfileID BIGSERIAL PRIMARY KEY,
    discordID     VARCHAR(50),
    discordTag    VARCHAR(50),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS subscriber CASCADE;
CREATE TABLE subscriber
(
    userProfileID BIGSERIAL,
    timerID       BIGSERIAL,
    PRIMARY KEY (timerID, userProfileID),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (timerID)
        REFERENCES timer (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);
